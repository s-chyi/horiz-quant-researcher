module.exports = {
  apps: [{
    name: 'akshare-service',
    script: './start.sh',
    cwd: '/opt/ai-agency/projects/horiz-quant-researcher/akshare-service',
    interpreter: '/bin/bash',
    autorestart: true,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
