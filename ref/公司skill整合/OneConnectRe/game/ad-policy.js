// Session-only interstitial request policy. Change values only after platform review.
window.oneConnectAdPolicy = {
  winEvery: 1,             // Request on every Nth win; 1 preserves existing behavior.
  showOnFailure: true,     // false skips the failure interstitial request.
  minIntervalSeconds: 0    // Minimum between requests sent to an available provider.
};
