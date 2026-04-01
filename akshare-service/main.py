"""
Horiz Quant Researcher — AKShare Financial Data Service
Provides A-share financial data via REST API using AKShare.

Port: 8901
"""

import re
import traceback
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

import akshare as ak
import pandas as pd
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Horiz AKShare Data Service",
    description="A-share financial data API powered by AKShare",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Caches ---
quote_cache = TTLCache(maxsize=500, ttl=60)         # 1 min
kline_cache = TTLCache(maxsize=200, ttl=300)         # 5 min
financial_cache = TTLCache(maxsize=200, ttl=86400)   # 24h
industry_cache = TTLCache(maxsize=50, ttl=86400)     # 24h
fund_flow_cache = TTLCache(maxsize=200, ttl=300)     # 5 min
shareholder_cache = TTLCache(maxsize=200, ttl=86400) # 24h
index_cache = TTLCache(maxsize=50, ttl=60)           # 1 min


def normalize_code(code: str) -> tuple[str, str]:
    """Normalize stock code. Returns (pure_code, market).
    600519 -> ('600519', 'sh')
    600519.SH -> ('600519', 'sh')
    000001.SZ -> ('000001', 'sz')
    """
    code = code.strip().upper()
    if '.' in code:
        parts = code.split('.')
        return parts[0], parts[1].lower()
    
    pure = code.lstrip('0') if len(code) > 6 else code
    # Determine market by code prefix
    if code.startswith('6') or code.startswith('5') or code.startswith('9'):
        return code, 'sh'
    elif code.startswith('0') or code.startswith('2') or code.startswith('3'):
        return code, 'sz'
    else:
        return code, 'sh'


def em_symbol(pure_code: str, market: str) -> str:
    """East Money format: SH600519 or SZ000001"""
    return f"{market.upper()}{pure_code}"


def safe_float(val) -> Optional[float]:
    """Safely convert to float."""
    if val is None or pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val) -> Optional[int]:
    """Safely convert to int."""
    if val is None or pd.isna(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def safe_str(val) -> Optional[str]:
    """Safely convert to string."""
    if val is None or pd.isna(val):
        return None
    return str(val)


def df_to_records(df: pd.DataFrame, limit: int = None) -> list[dict]:
    """Convert DataFrame to list of dicts with NaN handling."""
    if df is None or df.empty:
        return []
    if limit:
        df = df.head(limit)
    records = df.where(df.notna(), None).to_dict('records')
    # Convert numpy types
    clean = []
    for r in records:
        row = {}
        for k, v in r.items():
            k_str = str(k)
            if isinstance(v, (pd.Timestamp, datetime)):
                row[k_str] = v.isoformat()
            elif hasattr(v, 'item'):  # numpy scalar
                row[k_str] = v.item()
            else:
                row[k_str] = v
        clean.append(row)
    return clean


# --- Error handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__}
    )


# --- Health ---
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "akshare-data",
        "akshare_version": ak.__version__,
        "timestamp": datetime.now().isoformat(),
    }


# --- Quote ---
@app.get("/api/v1/quote/{code}")
async def get_quote(code: str):
    """实时行情: 股价、涨跌幅、成交量、市值、PE/PB (fast ~1s per stock)"""
    pure_code, market = normalize_code(code)
    cache_key = f"quote:{pure_code}"
    
    if cache_key in quote_cache:
        return quote_cache[cache_key]
    
    try:
        # Fast path: use individual stock APIs (~1s total vs ~90s for full scan)
        info_df = ak.stock_individual_info_em(symbol=pure_code)
        bid_df = ak.stock_bid_ask_em(symbol=pure_code)
        
        # Parse info (key-value format)
        info = {}
        if info_df is not None and not info_df.empty:
            for _, row in info_df.iterrows():
                info[str(row.get('item', ''))] = row.get('value')
        
        # Parse bid/ask
        bid = {}
        if bid_df is not None and not bid_df.empty:
            for _, row in bid_df.iterrows():
                bid[str(row.get('item', ''))] = row.get('value')
        
        price = safe_float(bid.get('最新'))
        prev_close = safe_float(info.get('最新'))  # info has latest too
        
        result = {
            "code": pure_code,
            "name": safe_str(info.get('股票简称')),
            "price": price,
            "change_pct": safe_float(bid.get('涨幅')),
            "change_amount": safe_float(bid.get('涨跌')),
            "volume": safe_int(bid.get('总手')),
            "amount": safe_float(bid.get('金额')),
            "turnover_rate": safe_float(bid.get('换手')),
            "volume_ratio": safe_float(bid.get('量比')),
            "total_market_cap": safe_float(info.get('总市值')),
            "circulating_market_cap": safe_float(info.get('流通市值')),
            "total_shares": safe_float(info.get('总股本')),
            "industry": safe_str(info.get('行业')),
            "pe_ratio": None,  # will compute below
            "pb_ratio": None,
            "source": "akshare/eastmoney",
            "updated_at": datetime.now().isoformat(),
        }
        
        # Try to get PE/PB from a fast supplementary call
        try:
            spot_df = ak.stock_individual_spot_xq(symbol=f"{'SH' if market == 'sh' else 'SZ'}{pure_code}")
            if spot_df is not None and not spot_df.empty:
                spot = {}
                for _, row in spot_df.iterrows():
                    spot[str(row.get('item', ''))] = row.get('value')
                result["pe_ratio"] = safe_float(spot.get('pe_ttm') or spot.get('市盈率'))
                result["pb_ratio"] = safe_float(spot.get('pb') or spot.get('市净率'))
        except Exception:
            # Fallback: compute PE from market_cap / net_profit if we have financial data
            pass
        
        quote_cache[cache_key] = result
        return result
    except Exception as e:
        # Ultimate fallback: full scan (slow but reliable)
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == pure_code]
            if row.empty:
                raise HTTPException(status_code=404, detail=f"Stock {pure_code} not found")
            r = row.iloc[0]
            result = {
                "code": pure_code,
                "name": safe_str(r.get('名称')),
                "price": safe_float(r.get('最新价')),
                "change_pct": safe_float(r.get('涨跌幅')),
                "change_amount": safe_float(r.get('涨跌额')),
                "volume": safe_int(r.get('成交量')),
                "amount": safe_float(r.get('成交额')),
                "turnover_rate": safe_float(r.get('换手率')),
                "pe_ratio": safe_float(r.get('市盈率-动态')),
                "pb_ratio": safe_float(r.get('市净率')),
                "total_market_cap": safe_float(r.get('总市值')),
                "circulating_market_cap": safe_float(r.get('流通市值')),
                "source": "akshare/eastmoney/full_scan",
                "updated_at": datetime.now().isoformat(),
            }
            quote_cache[cache_key] = result
            return result
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {e2}")


# --- K-Line ---
@app.get("/api/v1/kline/{code}")
async def get_kline(
    code: str,
    period: str = Query("daily", description="daily/weekly/monthly"),
    days: int = Query(250, description="Number of trading days"),
    adjust: str = Query("qfq", description="qfq=前复权, hfq=后复权, empty=不复权"),
):
    """日K线数据 (OHLCV)"""
    pure_code, market = normalize_code(code)
    cache_key = f"kline:{pure_code}:{period}:{days}:{adjust}"
    
    if cache_key in kline_cache:
        return kline_cache[cache_key]
    
    try:
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        end = datetime.now().strftime("%Y%m%d")
        
        df = ak.stock_zh_a_hist(
            symbol=pure_code, period=period,
            start_date=start, end_date=end,
            adjust=adjust if adjust else ""
        )
        
        if df is None or df.empty:
            return {"code": pure_code, "period": period, "data": [], "count": 0}
        
        df = df.tail(days)
        records = []
        for _, r in df.iterrows():
            records.append({
                "date": str(r.get('日期', '')),
                "open": safe_float(r.get('开盘')),
                "high": safe_float(r.get('最高')),
                "low": safe_float(r.get('最低')),
                "close": safe_float(r.get('收盘')),
                "volume": safe_int(r.get('成交量')),
                "amount": safe_float(r.get('成交额')),
                "turnover": safe_float(r.get('换手率')),
            })
        
        result = {
            "code": pure_code,
            "period": period,
            "adjust": adjust,
            "data": records,
            "count": len(records),
        }
        kline_cache[cache_key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch kline: {e}")


# --- Financials (Income Statement Summary) ---
@app.get("/api/v1/financials/{code}")
async def get_financials(code: str, limit: int = Query(8, description="Number of quarters")):
    """财务报表摘要: 营收/净利/毛利率/净利率/ROE"""
    pure_code, market = normalize_code(code)
    cache_key = f"fin:{pure_code}:{limit}"
    
    if cache_key in financial_cache:
        return financial_cache[cache_key]
    
    try:
        # Use stock_financial_abstract_ths (同花顺财务摘要)
        df = ak.stock_financial_abstract_ths(symbol=pure_code)
        
        if df is not None and not df.empty:
            # Sort by report date descending (latest first)
            if '报告期' in df.columns:
                df = df.sort_values('报告期', ascending=False)
            records = df_to_records(df, limit)
            result = {
                "code": pure_code,
                "data": records,
                "count": len(records),
                "source": "akshare/ths",
            }
            financial_cache[cache_key] = result
            return result
    except Exception:
        pass
    
    try:
        # Fallback: profit sheet from eastmoney
        symbol = em_symbol(pure_code, market)
        df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        if df is not None and not df.empty:
            # Extract key metrics
            records = []
            for _, r in df.head(limit).iterrows():
                records.append({
                    "report_date": safe_str(r.get("REPORT_DATE")),
                    "report_name": safe_str(r.get("REPORT_DATE_NAME")),
                    "total_revenue": safe_float(r.get("TOTAL_OPERATE_INCOME")),
                    "revenue_yoy": safe_float(r.get("TOTAL_OPERATE_INCOME_YOY")),
                    "operate_income": safe_float(r.get("OPERATE_INCOME")),
                    "operate_cost": safe_float(r.get("OPERATE_COST")),
                    "operate_profit": safe_float(r.get("OPERATE_PROFIT")),
                    "total_profit": safe_float(r.get("TOTAL_PROFIT")),
                    "net_profit": safe_float(r.get("NETPROFIT")),
                    "net_profit_yoy": safe_float(r.get("NETPROFIT_YOY")),
                    "parent_net_profit": safe_float(r.get("PARENT_NETPROFIT")),
                    "parent_net_profit_yoy": safe_float(r.get("PARENT_NETPROFIT_YOY")),
                    "deducted_net_profit": safe_float(r.get("DEDUCT_PARENT_NETPROFIT")),
                    "basic_eps": safe_float(r.get("BASIC_EPS")),
                    "sale_expense": safe_float(r.get("SALE_EXPENSE")),
                    "manage_expense": safe_float(r.get("MANAGE_EXPENSE")),
                    "finance_expense": safe_float(r.get("FINANCE_EXPENSE")),
                    "research_expense": safe_float(r.get("RESEARCH_EXPENSE")),
                })
            result = {
                "code": pure_code,
                "data": records,
                "count": len(records),
                "source": "akshare/eastmoney/profit_sheet",
                "note": "Key fields extracted from full profit statement",
            }
            financial_cache[cache_key] = result
            return result
    except Exception as e:
        pass
    
    return {"code": pure_code, "data": [], "source": "akshare", "note": "No financial data available"}


# --- Balance Sheet ---
@app.get("/api/v1/balance-sheet/{code}")
async def get_balance_sheet(code: str, limit: int = Query(4)):
    """资产负债表关键指标"""
    pure_code, market = normalize_code(code)
    cache_key = f"bs:{pure_code}:{limit}"
    
    if cache_key in financial_cache:
        return financial_cache[cache_key]
    
    try:
        df = ak.stock_balance_sheet_by_report_em(symbol=em_symbol(pure_code, market))
        if df is None or df.empty:
            return {"code": pure_code, "data": [], "note": "No data"}
        
        records = df_to_records(df, limit)
        result = {"code": pure_code, "data": records, "count": len(records), "source": "akshare"}
        financial_cache[cache_key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Balance sheet error: {e}")


# --- Cash Flow ---
@app.get("/api/v1/cash-flow/{code}")
async def get_cash_flow(code: str, limit: int = Query(4)):
    """现金流量表"""
    pure_code, market = normalize_code(code)
    cache_key = f"cf:{pure_code}:{limit}"
    
    if cache_key in financial_cache:
        return financial_cache[cache_key]
    
    try:
        df = ak.stock_cash_flow_sheet_by_report_em(symbol=em_symbol(pure_code, market))
        if df is None or df.empty:
            return {"code": pure_code, "data": [], "note": "No data"}
        
        records = df_to_records(df, limit)
        result = {"code": pure_code, "data": records, "count": len(records), "source": "akshare"}
        financial_cache[cache_key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cash flow error: {e}")


# --- DuPont / Financial Indicators ---
@app.get("/api/v1/indicators/{code}")
async def get_indicators(code: str):
    """财务指标 + 杜邦分析"""
    pure_code, market = normalize_code(code)
    cache_key = f"ind:{pure_code}"
    
    if cache_key in financial_cache:
        return financial_cache[cache_key]
    
    try:
        # Use stock_financial_abstract_ths for key indicators
        df = ak.stock_financial_abstract_ths(symbol=pure_code)
        if df is not None and not df.empty:
            if '报告期' in df.columns:
                df = df.sort_values('报告期', ascending=False)
            records = df_to_records(df, 8)
            result = {
                "code": pure_code,
                "data": records,
                "count": len(records),
                "source": "akshare/ths",
                "note": "Contains net_profit, revenue, eps, ROE etc. from THS financial abstract",
            }
            financial_cache[cache_key] = result
            return result
    except Exception:
        pass
    
    return {"code": pure_code, "data": [], "note": "No indicator data available"}


# --- Industry Classification ---
@app.get("/api/v1/industry/{code}")
async def get_industry(code: str):
    """行业分类 + 同行业公司"""
    pure_code, market = normalize_code(code)
    cache_key = f"industry:{pure_code}"
    
    if cache_key in industry_cache:
        return industry_cache[cache_key]
    
    try:
        # Get stock's industry
        df_all = ak.stock_board_industry_cons_em(symbol="白酒")  # This needs the industry name
        # Alternative: get the stock's info which includes industry
        
        # Better approach: search across all industries
        df_board = ak.stock_board_industry_name_em()
        
        if df_board is None or df_board.empty:
            return {"code": pure_code, "industry": None, "peers": []}
        
        # Find which industry contains this stock
        found_industry = None
        peers = []
        
        for _, row in df_board.iterrows():
            board_name = row.get('板块名称', '')
            try:
                df_cons = ak.stock_board_industry_cons_em(symbol=board_name)
                if df_cons is not None and not df_cons.empty:
                    if pure_code in df_cons['代码'].values:
                        found_industry = board_name
                        peers = df_cons[['代码', '名称']].head(20).to_dict('records')
                        break
            except:
                continue
        
        result = {
            "code": pure_code,
            "industry": found_industry,
            "peers": peers,
            "source": "akshare/eastmoney",
        }
        industry_cache[cache_key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Industry error: {e}")


# --- Fund Flow ---
@app.get("/api/v1/fund-flow/{code}")
async def get_fund_flow(code: str):
    """资金流向"""
    pure_code, market = normalize_code(code)
    cache_key = f"flow:{pure_code}"
    
    if cache_key in fund_flow_cache:
        return fund_flow_cache[cache_key]
    
    try:
        df = ak.stock_individual_fund_flow(stock=pure_code, market=market)
        if df is None or df.empty:
            return {"code": pure_code, "data": [], "note": "No fund flow data"}
        
        records = df_to_records(df, 20)
        result = {
            "code": pure_code,
            "data": records,
            "count": len(records),
            "source": "akshare/eastmoney",
        }
        fund_flow_cache[cache_key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fund flow error: {e}")


# --- Shareholders ---
@app.get("/api/v1/shareholders/{code}")
async def get_shareholders(code: str):
    """十大股东"""
    pure_code, market = normalize_code(code)
    cache_key = f"holders:{pure_code}"
    
    if cache_key in shareholder_cache:
        return shareholder_cache[cache_key]
    
    try:
        df = ak.stock_main_stock_holder(stock=pure_code)
        if df is None or df.empty:
            return {"code": pure_code, "data": [], "note": "No shareholder data"}
        
        records = df_to_records(df, 20)
        result = {
            "code": pure_code,
            "data": records,
            "count": len(records),
            "source": "akshare",
        }
        shareholder_cache[cache_key] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shareholders error: {e}")


# --- Index ---
@app.get("/api/v1/index/{code}")
async def get_index(code: str):
    """指数行情 (沪深300=000300, 上证=000001, 创业板=399006)"""
    cache_key = f"index:{code}"
    
    if cache_key in index_cache:
        return index_cache[cache_key]
    
    try:
        df = ak.stock_zh_index_spot_em()
        if df is None or df.empty:
            raise HTTPException(status_code=500, detail="Failed to fetch index data")
        
        row = df[df['代码'] == code]
        if row.empty:
            # Try partial match
            row = df[df['代码'].str.contains(code)]
        
        if row.empty:
            raise HTTPException(status_code=404, detail=f"Index {code} not found")
        
        r = row.iloc[0]
        result = {
            "code": safe_str(r.get('代码')),
            "name": safe_str(r.get('名称')),
            "price": safe_float(r.get('最新价')),
            "change_pct": safe_float(r.get('涨跌幅')),
            "change_amount": safe_float(r.get('涨跌额')),
            "volume": safe_float(r.get('成交量')),
            "amount": safe_float(r.get('成交额')),
            "open": safe_float(r.get('今开')),
            "high": safe_float(r.get('最高')),
            "low": safe_float(r.get('最低')),
            "prev_close": safe_float(r.get('昨收')),
            "source": "akshare/eastmoney",
        }
        index_cache[cache_key] = result
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8901)
