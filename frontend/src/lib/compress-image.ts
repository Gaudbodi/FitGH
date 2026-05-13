// Image-compression helper — Phase 4 Plan 04 (P4-C.1).
//
// Wraps `browser-image-compression` (a 25 KB minified+gzipped client lib)
// with our compression options:
//   maxSizeMB: 0.5         — hard cap so a 4 MB iPhone photo lands at
//                            200-400 KB, well within the FE→BFF egress.
//   maxWidthOrHeight: 1024 — Sonnet 4.6 processes 1024×768 in the same
//                            latency budget as smaller images.
//   fileType: image/jpeg   — strip metadata (EXIF) + standardise mime.
//   initialQuality: 0.85   — minimal visual difference; large size win.
//   useWebWorker: true     — keeps the compression off the main thread
//                            so the UI stays interactive on lower-end Android.
//
// CRITICAL — D-LAZY-COMPRESS: this module dynamic-imports the library
// inside compressMealImage so the dashboard's First Load JS never pays
// the ~25 KB browser-image-compression cost. Until the user taps
// "Snap a meal", the lib is not in any chunk the dashboard loads.

export const COMPRESS_OPTS = {
  maxSizeMB: 0.5,
  maxWidthOrHeight: 1024,
  fileType: "image/jpeg" as const,
  initialQuality: 0.85,
  useWebWorker: true,
};

export async function compressMealImage(file: File): Promise<File> {
  const mod = await import("browser-image-compression");
  const imageCompression = mod.default;
  const compressed = await imageCompression(file, COMPRESS_OPTS);
  return compressed as File;
}
