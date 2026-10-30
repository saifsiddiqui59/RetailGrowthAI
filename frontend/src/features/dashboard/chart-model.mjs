export function verifiedCounts(values, labels) {
  if (!Array.isArray(values) || !Array.isArray(labels) || values.length !== labels.length ||
      !values.length || !values.every(v => Number.isSafeInteger(v) && v >= 0)) return null
  return { labels, datasets: [{ label: 'Verified records', data: values,
    backgroundColor: ['#168467', '#4d8fc2', '#e2ab57', '#647d9a', '#7f6db7', '#62aaa6'].slice(0, values.length),
    borderRadius: 8, maxBarThickness: 46 }] }
}

