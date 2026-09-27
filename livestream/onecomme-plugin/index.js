// わんコメ → AIキャラ応答サーバー のブリッジ
// わんコメの「プラグイン」フォルダにこのフォルダごと置き、設定 > プラグイン から有効化する。
const http = require('http')

const SERVER = { host: '127.0.0.1', port: 5005, path: '/comment' }

function forward(payload) {
  const body = JSON.stringify(payload)
  const req = http.request({
    ...SERVER,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    timeout: 3000,
  })
  req.on('error', () => {}) // サーバー停止中（配信時間外）は黙って捨てる
  req.on('timeout', () => req.destroy())
  req.end(body)
}

module.exports = {
  name: 'AIキャラ応答ブリッジ',
  uid: 'ai-vtuber-bridge',
  version: '1.1.0',
  author: 'shacho',
  url: '',
  permissions: ['comments'],
  defaultState: {},
  init() {},
  subscribe(type, ...args) {
    if (type !== 'comments') return
    const comments = args[0] || []
    for (const c of comments) {
      const d = c.data || {}
      forward({
        text: d.comment || '',
        name: d.displayName || d.name || '',
        userId: d.userId || d.id || '',
        service: c.service || '',
        isOwner: !!d.isOwner,
        hasGift: !!d.hasGift,
        price: d.price || 0, // スパチャ等の金額（あれば）
      })
    }
  },
}
