
// Quick API test script
// Run with: node test-api.js
// Tests connectivity to Backend API (single source architecture)

import axios from 'axios';

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Test Backend API Health
async function testBackendAPI() {
  console.log('\n=== Testing Backend API ===');
  console.log(`Endpoint: ${API_BASE_URL}`);
  
  try {
    const response = await axios.get(`${API_BASE_URL}/etl-jobs/`, {
      timeout: 5000,
    });
    console.log(`✅ Backend API working! Status: ${response.status}`);
    console.log('Response:', JSON.stringify(response.data, null, 2));
  } catch (error) {
    if (error.response?.status === 404) {
      console.log('⚠️  Backend API endpoint not found (404) - This is expected if backend is not implemented');
    } else if (error.code === 'ECONNREFUSED') {
      console.log('⚠️  Backend API not running - This is expected if backend is not set up');
    } else {
      console.log(`⚠️  Backend API error: ${error.message}`);
    }
  }
}

// Test Overpass Proxy through Backend
async function testOverpassProxy() {
  console.log('\n=== Testing Overpass Proxy ===');
  console.log(`Endpoint: ${API_BASE_URL}/overpass/facilities`);
  
  try {
    const response = await axios.post(`${API_BASE_URL}/overpass/facilities`, {}, {
      timeout: 60000,
    });
    
    if (response.data && response.data.facilities) {
      console.log(`✅ Overpass proxy working! Found ${response.data.facilities.length} facilities`);
      if (response.data.facilities.length > 0) {
        console.log('Sample facility:', JSON.stringify(response.data.facilities[0], null, 2));
      }
    } else {
      console.log('⚠️  Overpass proxy responded but no facilities found');
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('❌ Connection refused - Is the backend server running?');
    } else if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
      console.log('❌ Request timeout - Backend or Overpass API may be slow');
    } else if (error.response) {
      console.log(`❌ Error: ${error.response.status} ${error.response.statusText}`);
      if (error.response.data) {
        console.log('Response data:', error.response.data);
      }
    } else {
      console.log(`❌ Error: ${error.message}`);
    }
  }
}

// Test Overpass Proxy Health Check
async function testOverpassHealth() {
  console.log('\n=== Testing Overpass Proxy Health ===');
  console.log(`Endpoint: ${API_BASE_URL}/overpass/health`);
  
  try {
    const response = await axios.get(`${API_BASE_URL}/overpass/health`, {
      timeout: 10000,
    });
    
    console.log(`✅ Overpass health check working! Status: ${response.status}`);
    console.log('Health status:', JSON.stringify(response.data, null, 2));
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('❌ Connection refused - Is the backend server running?');
    } else if (error.response) {
      console.log(`❌ Error: ${error.response.status} ${error.response.statusText}`);
      if (error.response.data) {
        console.log('Response data:', error.response.data);
      }
    } else {
      console.log(`❌ Error: ${error.message}`);
    }
  }
}

// Run tests
(async () => {
  await testBackendAPI();
  await testOverpassHealth();
  await testOverpassProxy();
  console.log('\n=== Test Complete ===\n');
})();

