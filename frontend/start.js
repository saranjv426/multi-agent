#!/usr/bin/env node

/**
 * Startup script for the Roof Design Validation Frontend
 */

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

function checkEnvironment() {
    console.log('Checking environment configuration...');
    
    // Check if .env.local exists
    const envFile = path.join(__dirname, '.env.local');
    if (!fs.existsSync(envFile)) {
        console.log('.env.local file not found. Creating from template...');
        
        const envTemplate = `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`;
        
        fs.writeFileSync(envFile, envTemplate);
        console.log('Created .env.local file');
    }
    
    console.log('Environment configuration ready');
    return true;
}

function checkDependencies() {
    console.log('Checking dependencies...');
    
    // Check if node_modules exists
    if (!fs.existsSync(path.join(__dirname, 'node_modules'))) {
        console.log('node_modules not found. Installing dependencies...');
        
        try {
            console.log('Running npm install...');
            execSync('npm install', { stdio: 'inherit', cwd: __dirname });
            console.log('Dependencies installed successfully');
            return true;
        } catch (error) {
            console.error('Failed to install dependencies:', error.message);
            return false;
        }
    }
    
    console.log('Dependencies are ready');
    return true;
}

function startServer() {
    console.log('Starting Roof Design Validation Frontend...');
    console.log('Frontend will be available at: http://localhost:3000');
    console.log('Press Ctrl+C to stop the server');
    console.log('-'.repeat(50));
    
    const dev = spawn('npm', ['run', 'dev'], {
        stdio: 'inherit',
        cwd: __dirname,
        shell: true
    });
    
    dev.on('close', (code) => {
        if (code === 0) {
            console.log('Frontend server stopped cleanly');
        } else {
            console.log(`Frontend server exited with code ${code}`);
        }
    });
    
    dev.on('error', (error) => {
        console.error('Failed to start frontend server:', error.message);
    });
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n Shutting down frontend server...');
        dev.kill('SIGINT');
        process.exit(0);
    });
}

function main() {
    console.log('Roof Design Validation Frontend');
    console.log('='.repeat(40));
    
    // Check environment
    if (!checkEnvironment()) {
        process.exit(1);
    }
    
    // Check and install dependencies
    if (!checkDependencies()) {
        console.log('Dependency setup failed. Please install manually:');
        console.log('   npm install');
        process.exit(1);
    }
    
    // Start development server
    startServer();
}

if (require.main === module) {
    main();
}