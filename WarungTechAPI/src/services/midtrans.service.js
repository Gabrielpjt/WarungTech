const midtransClient = require('midtrans-client');

// Snap API (untuk membuat transaction token)
const snap = new midtransClient.Snap({
    isProduction: process.env.MIDTRANS_IS_PRODUCTION === 'true',
    serverKey: process.env.MIDTRANS_SERVER_KEY,
    clientKey: process.env.MIDTRANS_CLIENT_KEY
});

// Core API (untuk cek status & webhook)
const coreApi = new midtransClient.CoreApi({
    isProduction: process.env.MIDTRANS_IS_PRODUCTION === 'true',
    serverKey: process.env.MIDTRANS_SERVER_KEY
});

module.exports = {
    createTransaction: async (params) => {
        return await snap.createTransaction(params);
    },
    getTransactionStatus: async (orderId) => {
        return await coreApi.transaction.status(orderId);
    },
    handleNotification: async (notificationBody) => {
        return await coreApi.transaction.notification(notificationBody);
    }
};
