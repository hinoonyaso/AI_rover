/** Compare four color-camera intrinsics without asserting device identity or quality.
 * 한글: 장치 동일성이나 품질을 단정하지 않고 네 컬러 내부값을 비교한다. */
export function cameraComparison(candidate, current) {
  if (!candidate || !current) return {status: 'missing'};
  if (!Number.isInteger(candidate.width) || !Number.isInteger(candidate.height) || candidate.width <= 0 || candidate.height <= 0 || candidate.width !== current.width || candidate.height !== current.height) return {status: 'resolution'};
  const matrix = candidate.camera_matrix;
  if (!Array.isArray(matrix) || matrix.length !== 3 || matrix.some(row => !Array.isArray(row) || row.length !== 3) || !Array.isArray(current.matrix) || current.matrix.length !== 9) return {status: 'invalid'};
  const values = [['fx', 0, 0], ['fy', 1, 1], ['cx', 0, 2], ['cy', 1, 2]].map(([name, row, col]) => {
    const measured = matrix[row][col], existing = current.matrix[row * 3 + col];
    return {name, measured, existing, difference: measured - existing};
  });
  if (values.some(item => !Number.isFinite(item.measured) || !Number.isFinite(item.existing)) || values.slice(0, 2).some(item => item.measured <= 0 || item.existing <= 0)) return {status: 'invalid'};
  return {status: 'ok', values};
}
