// Utility functions for formatting data

/**
 * Formats a skill rate and rate type into a display string.
 * @param {object} item - The listing item object.
 * @param {number} item.rate - The skill rate.
 * @param {string} item.rate_type - The type of rate ('hourly' or 'fixed').
 * @returns {string} The formatted rate string.
 */
export function formatRate(item) {
  if (item.rate == null) return 'N/A';
  return `$${parseFloat(item.rate).toFixed(2)}${item.rate_type === 'fixed' ? ' (fixed)' : '/hr'}`;
}