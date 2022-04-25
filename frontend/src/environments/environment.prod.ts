export const environment = {
  production: true,
  baseUrl: '/api',
  websocket: {
    url: window.location.protocol === 'https:'
      ? 'wss://' + location.host + '/socket'
      : 'ws://' + location.host + '/socket',
    retry: 10
  }
};
