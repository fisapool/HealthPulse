// Quick API test script
// Run with: node test-api.js
// Tests connectivity to Overpass API and Backend API

import axios from 'axios';

const OVERPASS_API_URL = process.env.VITE_OVERPASS_API_URL || 'http://192.168.0.145:8083/api/interpreter';
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Test Overpass API
async function testOverpassAPI() {
  console.log('\n=== Testing Overpass API ===');
  console.log(`Endpoint: ${OVERPASS_API_URL}`);
  
  const query = `
    [out:json][timeout:10];
    (
      node["amenity"="hospital"](0.855,98.942,7.363,119.267);
      way["amenity"="hospital"](0.855,98.942,7.363,119.267);
    );
    out center meta;
  `.trim();

  try {
    const response = await axios.post(OVERPASS_API_URL, query, {
      headers: { 'Content-Type': 'text/plain' },
      timeout: 30000,
    });
    
    if (response.data && response.data.elements) {
      console.log(`✅ Overpass API working! Found ${response.data.elements.length} elements`);
      if (response.data.elements.length > 0) {
        console.log('Sample element:', JSON.stringify(response.data.elements[0], null, 2));
      }
    } else {
      console.log('⚠️  Overpass API responded but no elements found');
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('❌ Connection refused - Is the Overpass API server running?');
    } else if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
      console.log('❌ Request timeout - API may be slow or unreachable');
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

// Test Backend API
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

// Run tests
(async () => {
  await testOverpassAPI();
  await testBackendAPI();
  console.log('\n=== Test Complete ===\n');
})();

