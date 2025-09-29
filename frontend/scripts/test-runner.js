#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// Test runner script for comprehensive frontend testing

const runCommand = (command, args, options = {}) => {
  return new Promise((resolve, reject) => {
    console.log(`\n🚀 Running: ${command} ${args.join(' ')}\n`);
    
    const child = spawn(command, args, {
      stdio: 'inherit',
      shell: true,
      ...options,
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });
    
    child.on('error', reject);
  });
};

const runTests = async () => {
  try {
    console.log('📋 Starting Frontend Test Suite...\n');
    
    // 1. Run unit tests
    console.log('1️⃣ Running Unit Tests...');
    await runCommand('npm', ['run', 'test']);
    
    // 2. Run integration tests
    console.log('\n2️⃣ Running Integration Tests...');
    await runCommand('npm', ['run', 'test:integration']);
    
    // 3. Generate coverage report
    console.log('\n3️⃣ Generating Coverage Report...');
    await runCommand('npm', ['run', 'test:coverage']);
    
    // 4. Run linting
    console.log('\n4️⃣ Running Linting...');
    await runCommand('npm', ['run', 'lint']);
    
    // 5. Check formatting
    console.log('\n5️⃣ Checking Code Formatting...');
    await runCommand('npm', ['run', 'format:check']);
    
    console.log('\n✅ All tests passed successfully!');
    console.log('\n📊 Test Summary:');
    console.log('   ✓ Unit Tests');
    console.log('   ✓ Integration Tests');
    console.log('   ✓ Code Coverage');
    console.log('   ✓ Linting');
    console.log('   ✓ Code Formatting');
    
    console.log('\n📁 Coverage report available at: coverage/index.html');
    
  } catch (error) {
    console.error('\n❌ Test suite failed:', error.message);
    process.exit(1);
  }
};

const runE2ETests = async () => {
  try {
    console.log('🎭 Starting E2E Tests...\n');
    
    // Check if Cypress is available
    console.log('1️⃣ Running End-to-End Tests...');
    await runCommand('npm', ['run', 'test:e2e']);
    
    console.log('\n✅ E2E tests passed successfully!');
    
  } catch (error) {
    console.error('\n❌ E2E tests failed:', error.message);
    process.exit(1);
  }
};

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0];

switch (command) {
  case 'unit':
    runCommand('npm', ['run', 'test']).catch(() => process.exit(1));
    break;
  case 'integration':
    runCommand('npm', ['run', 'test:integration']).catch(() => process.exit(1));
    break;
  case 'e2e':
    runE2ETests();
    break;
  case 'coverage':
    runCommand('npm', ['run', 'test:coverage']).catch(() => process.exit(1));
    break;
  case 'all':
  default:
    runTests();
    break;
}