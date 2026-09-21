// Distinct colors for structure markers, shared by the 3D viewer and the list
// so the same marker is identifiable in both places.
export const MARKER_COLORS = [
  "#f5222d",
  "#fa8c16",
  "#faad14",
  "#52c41a",
  "#eb2f96",
  "#722ed1",
  "#13c2c2",
  "#a0d911",
];

export function markerColor(index: number): string {
  return MARKER_COLORS[index % MARKER_COLORS.length];
}
