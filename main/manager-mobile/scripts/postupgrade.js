// # Running `pnpm upgrade` upgrades the `uniapp`-related dependencies
// # After upgrading, many unused dependencies are added automatically; they must be removed to reduce the bundle size
// # Just run the command below

const { exec } = require('node:child_process')

// Define the command to run
const dependencies = [
  '@dcloudio/uni-app-harmony',
  // TODO: manually remove or comment out any platform Mini Programs you do not need
  '@dcloudio/uni-mp-alipay',
  '@dcloudio/uni-mp-baidu',
  '@dcloudio/uni-mp-jd',
  '@dcloudio/uni-mp-kuaishou',
  '@dcloudio/uni-mp-lark',
  '@dcloudio/uni-mp-qq',
  '@dcloudio/uni-mp-toutiao',
  '@dcloudio/uni-mp-xhs',
  '@dcloudio/uni-quickapp-webview',
  // Comment out the following if using the i18n template
  'vue-i18n',
]

// Run the command with exec
exec(`pnpm un ${dependencies.join(' ')}`, (error, stdout, stderr) => {
  if (error) {
    // Print the error message if an error occurs
    console.error(`Execution error: ${error}`)
    return
  }
  // Print the normal output
  console.log(`stdout: ${stdout}`)
  // Print the error output as well
  console.error(`stderr: ${stderr}`)
})
