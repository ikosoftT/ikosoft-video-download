module.exports = function handler(req, res) {
  const raw = (process.env.DOWNLOAD_BACKEND_URL || '').trim();
  let backend = '';
  try {
    const url = new URL(raw);
    if (url.protocol === 'https:' && !url.username && !url.password && url.pathname === '/' && !url.search && !url.hash) backend = url.origin;
  } catch {}
  const paypal = (process.env.PAYPAL_SUPPORT_URL || '').trim();
  let paypalUrl = 'https://www.paypal.com/', configured = false;
  try {
    const url = new URL(paypal);
    if (url.protocol === 'https:' && ['paypal.com','www.paypal.com','paypal.me','www.paypal.me'].includes(url.hostname) && !url.username && !url.password && !url.port) {
      paypalUrl = url.href;
      configured = !(['paypal.com','www.paypal.com'].includes(url.hostname) && url.pathname === '/' && !url.search);
    }
  } catch {}
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({backend_url:backend, backend_required:true, backend_temporary:backend.endsWith(".trycloudflare.com"), backend_render:backend.endsWith(".onrender.com"), paypal_url:paypalUrl, paypal_configured:configured});
};
