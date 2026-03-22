// Rwanda administrative boundaries — simplified polygons (WGS84)
// Provinces: 5 provinces per official Rwanda administration
// Districts: centroid coordinates for all 30 districts

export const RWANDA_BOUNDS: [[number, number], [number, number]] = [
  [-2.84, 28.86], // SW
  [-1.05, 30.90], // NE
];

// Province bounding boxes for fly-to animation
export const PROVINCE_BOUNDS: Record<string, [[number, number], [number, number]]> = {
  northern: [[-1.84, 29.05], [-1.06, 30.22]],
  eastern:  [[-2.84, 29.68], [-1.06, 30.90]],
  southern: [[-2.84, 28.86], [-1.70, 30.22]],
  western:  [[-2.73, 28.86], [-1.22, 29.52]],
  kigali:   [[-2.09, 29.83], [-1.77, 30.19]],
};

// Province centroids for labels
export const PROVINCE_CENTROIDS: Record<string, [number, number]> = {
  northern: [-1.40, 29.85],
  eastern:  [-2.00, 30.55],
  southern: [-2.28, 29.55],
  western:  [-1.98, 29.18],
  kigali:   [-1.94, 30.05],
};

// Simplified province polygon GeoJSON
// Coordinates: [longitude, latitude]
export const RWANDA_PROVINCES_GEO = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { key: "kigali", name: "Kigali City" },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [29.88, -1.84],
          [30.08, -1.77],
          [30.17, -1.84],
          [30.19, -2.00],
          [30.08, -2.09],
          [29.89, -2.03],
          [29.83, -1.92],
          [29.88, -1.84],
        ]],
      },
    },
    {
      type: "Feature",
      properties: { key: "northern", name: "Northern Province" },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [29.08, -1.22],
          [29.58, -1.06],
          [30.20, -1.55],
          [30.08, -1.77],
          [29.88, -1.84],
          [29.68, -1.73],
          [29.52, -1.70],
          [29.30, -1.57],
          [29.08, -1.45],
          [29.08, -1.22],
        ]],
      },
    },
    {
      type: "Feature",
      properties: { key: "western", name: "Western Province" },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [29.08, -1.22],
          [29.08, -1.45],
          [29.30, -1.57],
          [29.52, -1.70],
          [29.40, -1.91],
          [29.24, -2.15],
          [29.08, -2.41],
          [28.92, -2.63],
          [28.86, -2.73],
          [28.90, -2.28],
          [28.86, -1.90],
          [28.92, -1.52],
          [29.02, -1.28],
          [29.08, -1.22],
        ]],
      },
    },
    {
      type: "Feature",
      properties: { key: "southern", name: "Southern Province" },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [29.52, -1.70],
          [29.68, -1.73],
          [29.88, -1.84],
          [29.83, -1.92],
          [29.89, -2.03],
          [30.08, -2.09],
          [30.22, -2.35],
          [30.12, -2.57],
          [30.22, -2.84],
          [29.58, -2.84],
          [29.20, -2.84],
          [28.86, -2.73],
          [28.92, -2.63],
          [29.08, -2.41],
          [29.24, -2.15],
          [29.40, -1.91],
          [29.52, -1.70],
        ]],
      },
    },
    {
      type: "Feature",
      properties: { key: "eastern", name: "Eastern Province" },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [30.20, -1.55],
          [30.50, -1.08],
          [30.90, -1.08],
          [30.90, -2.42],
          [30.78, -2.84],
          [30.22, -2.84],
          [30.12, -2.57],
          [30.22, -2.35],
          [30.08, -2.09],
          [30.19, -2.00],
          [30.17, -1.84],
          [30.08, -1.77],
          [30.20, -1.55],
        ]],
      },
    },
  ],
} as const;

// District capitals — lat/lng for circle markers
export const DISTRICT_MARKERS: {
  name: string;
  province: string;
  lat: number;
  lng: number;
}[] = [
  // Northern Province
  { name: "Musanze",   province: "northern", lat: -1.498, lng: 29.635 },
  { name: "Burera",    province: "northern", lat: -1.370, lng: 29.840 },
  { name: "Gakenke",   province: "northern", lat: -1.698, lng: 29.720 },
  { name: "Gicumbi",   province: "northern", lat: -1.572, lng: 30.072 },
  { name: "Rulindo",   province: "northern", lat: -1.748, lng: 29.934 },
  // Eastern Province
  { name: "Nyagatare", province: "eastern",  lat: -1.302, lng: 30.328 },
  { name: "Gatsibo",   province: "eastern",  lat: -1.585, lng: 30.424 },
  { name: "Kayonza",   province: "eastern",  lat: -1.873, lng: 30.651 },
  { name: "Kirehe",    province: "eastern",  lat: -2.154, lng: 30.685 },
  { name: "Ngoma",     province: "eastern",  lat: -2.148, lng: 30.448 },
  { name: "Rwamagana", province: "eastern",  lat: -1.950, lng: 30.430 },
  { name: "Bugesera",  province: "eastern",  lat: -2.177, lng: 30.152 },
  // Southern Province
  { name: "Huye",      province: "southern", lat: -2.598, lng: 29.740 },
  { name: "Gisagara",  province: "southern", lat: -2.620, lng: 29.830 },
  { name: "Nyaruguru", province: "southern", lat: -2.718, lng: 29.633 },
  { name: "Nyamagabe", province: "southern", lat: -2.518, lng: 29.532 },
  { name: "Muhanga",   province: "southern", lat: -2.084, lng: 29.752 },
  { name: "Ruhango",   province: "southern", lat: -2.217, lng: 29.782 },
  { name: "Kamonyi",   province: "southern", lat: -2.003, lng: 29.882 },
  { name: "Nyanza",    province: "southern", lat: -2.352, lng: 29.732 },
  // Western Province
  { name: "Rubavu",    province: "western",  lat: -1.682, lng: 29.340 },
  { name: "Nyabihu",   province: "western",  lat: -1.600, lng: 29.482 },
  { name: "Ngororero", province: "western",  lat: -1.868, lng: 29.451 },
  { name: "Rutsiro",   province: "western",  lat: -2.001, lng: 29.318 },
  { name: "Karongi",   province: "western",  lat: -2.118, lng: 29.338 },
  { name: "Nyamasheke",province: "western",  lat: -2.348, lng: 29.002 },
  { name: "Rusizi",    province: "western",  lat: -2.598, lng: 28.940 },
  // Kigali City
  { name: "Gasabo",    province: "kigali",   lat: -1.875, lng: 30.102 },
  { name: "Kicukiro",  province: "kigali",   lat: -1.980, lng: 30.072 },
  { name: "Nyarugenge",province: "kigali",   lat: -1.948, lng: 30.042 },
];
