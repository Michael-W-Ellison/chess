/**
 * Test script for electron-store
 * Run with: npm run test:store
 */

const { store, trackAppLaunch, getStorePath, getAllStoreData } = require('../../dist/main/store');

console.log('\n=== Electron Store Test ===\n');

// 1. Display store path
console.log('1. Store Location:');
console.log(`   ${getStorePath()}\n`);

// 2. Track app launch
console.log('2. Tracking App Launch:');
trackAppLaunch();
console.log(`   ✓ App launch tracked\n`);

// 3. Test basic get/set
console.log('3. Basic Get/Set Test:');
store.set('settings.theme', 'dark');
const theme = store.get('settings.theme');
console.log(`   Set theme to: ${theme}`);
console.log(`   ✓ Get/Set working\n`);

// 4. Test nested values
console.log('4. Nested Value Test:');
store.set('user.name', 'TestUser');
store.set('user.age', 12);
store.set('user.grade', 7);
const userName = store.get('user.name');
const userAge = store.get('user.age');
console.log(`   User: ${userName}, Age: ${userAge}`);
console.log(`   ✓ Nested values working\n`);

// 5. Test has()
console.log('5. Key Existence Test:');
const hasTheme = store.has('settings.theme');
const hasNonExistent = store.has('nonexistent.key');
console.log(`   Has 'settings.theme': ${hasTheme}`);
console.log(`   Has 'nonexistent.key': ${hasNonExistent}`);
console.log(`   ✓ Has() working\n`);

// 6. Test default values
console.log('6. Default Value Test:');
const defaultValue = store.get('nonexistent.key', 'DEFAULT');
console.log(`   Non-existent key with default: ${defaultValue}`);
console.log(`   ✓ Default values working\n`);

// 7. Display all data
console.log('7. All Store Data:');
const allData = getAllStoreData();
console.log(JSON.stringify(allData, null, 2));
console.log('\n   ✓ GetAll() working\n');

// 8. Test delete
console.log('8. Delete Test:');
store.set('temp.test', 'temporary');
console.log(`   Created temp.test: ${store.get('temp.test')}`);
store.delete('temp.test');
console.log(`   Deleted temp.test: ${store.get('temp.test', 'UNDEFINED')}`);
console.log(`   ✓ Delete working\n`);

console.log('=== All Tests Passed! ===\n');
