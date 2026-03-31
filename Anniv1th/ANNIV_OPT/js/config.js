// ============================================================
//  !! SEMUA KUSTOMISASI DI SINI !!
//
//  File ini berisi semua konten yang perlu kamu edit:
//  - Tanggal jadian
//  - Teka-teki & jawaban
//  - Emoji memory card game
//  - Galeri foto & video
// ============================================================

const CFG = {

  // ----------------------------------------------------------
  //  TANGGAL JADIAN (YYYY-MM-DD)
  // ----------------------------------------------------------
  startDate: new Date("2025-04-01"),

  // ----------------------------------------------------------
  //  TEKA-TEKI
  //  type: "riddle"   → isi jawaban di `ans` (huruf kecil semua)
  //  type: "choice"   → isi pilihan di `opts`, index jawaban di `correct`
  //  type: "scramble" → isi kata di `word` (huruf besar)
  // ----------------------------------------------------------
  puzzles: [
    {
      type: "riddle",
      num: "Teka-Teki 1 / 4",
      emoji: "",
      q: "Kalau kita lagi bingung meh ngapain, dan pengen eksplor hal baru. Hobi kita bersama apa? (1 kata)",
      ans: "kulineran",
      hint: "💡 Petunjuk: Berhubungan sama perut... dan perut"
    },
    {
      type: "riddle",
      num: "Teka-Teki 2 / 4",
      emoji: "",
      q: "Apa kata yang sering kita ucapin tapi jarang kita lakuin? (1 kata)",
      ans: "olahraga",
      hint: "💡 Petunjuk: Outdoor, lebih ke pagi dan sore"
    },
    {
      type: "riddle",
      num: "Teka-Teki 3 / 4",
      emoji: "",
      q: "Tiap kali foto bareng, tanpa suruhan pun tangane kita udah otomatis sama posenya. Pose foto andalan kita apa? (2 kata)",
      ans: "dua jari",
      hint: "💡 Petunjuk: presiden kita!"
    },
    {
      type: "riddle",
      num: "Teka-Teki 4 / 4",
      emoji: "",
      q: "Awalnya makanan favoritmu — tapi lama-lama jadi favorit kita berdua juga. Makanan apa itu? (1 kata)",
      ans: "mie",
      hint: "💡 Petunjuk: Panjang, kenyal, dan bikin kangen 🍜"
    }
  ],

  // ----------------------------------------------------------
  //  MEMORY CARD GAME
  //  Ganti emoji sesuai keinginan (harus 8 pasang = 8 emoji)
  // ----------------------------------------------------------
  cardEmojis: ["💻", "🐛", "🧪", "🚀", "⚙️", "🔧", "☕", "📦"],

  // ----------------------------------------------------------
  //  GALERI FOTO & VIDEO — MASONRY GRID
  //
  //  size: "sm"   = 1×1  (default)
  //        "tall" = 1×2  (tinggi)
  //        "wide" = 2×1  (lebar — bagus untuk COLLAGE & video)
  //        "big"  = 2×2  (featured — untuk momen spesial)
  //
  //  month: label bulan yang muncul sebagai pemisah
  // ----------------------------------------------------------
  gallery: [
    // ── Feb 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250208_204240_950.jpg",  type: "photo", size: "sm",   month: "Feb 2025", cap: "Feb 2025" },
    { src: "asset/anniv/IMG_20250215_054709_553.jpg",  type: "photo", size: "tall", cap: "Feb 2025" },
    { src: "asset/anniv/IMG_20250226_183540_170.jpg",  type: "photo", size: "sm",   cap: "Feb 2025" },
    // ── Mar 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250301_161057_146.jpg",  type: "photo", size: "sm",   month: "Mar 2025", cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250301_203308_345.jpg",  type: "photo", size: "tall", cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250304_163718_360-COLLAGE.jpg", type: "photo", size: "wide", cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250305_190515_809.jpg",  type: "photo", size: "sm",   cap: "Mar 2025" },
    { src: "asset/anniv/VID_20250308_155122.mp4",      type: "video", size: "wide", cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250310_200628_113.jpg",  type: "photo", size: "tall", cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250315_062515_453.jpg",  type: "photo", size: "sm",   cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250315_070107_689.jpg",  type: "photo", size: "sm",   cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250315_191629_355.jpg",  type: "photo", size: "tall", cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250316_180035_332.jpg",  type: "photo", size: "sm",   cap: "Mar 2025" },
    { src: "asset/anniv/IMG_20250323_101014_881.jpg",  type: "photo", size: "sm",   cap: "Mar 2025" },
    { src: "asset/anniv/VID_20250323_152950.mp4",      type: "video", size: "wide", cap: "Mar 2025" },
    // ── 1 April 2025 — Hari Jadian! ───────────────────────
    { src: "asset/anniv/IMG_20250401_070107_411-COLLAGE.jpg", type: "photo", size: "wide", month: "1 April 2025 — Hari Jadian 🎉", cap: "1 April 2025" },
    { src: "asset/anniv/IMG_20250401_081223_256.jpg",  type: "photo", size: "big",  cap: "Hari Jadian! 💕" },
    { src: "asset/anniv/IMG_20250401_083407_783-COLLAGE.jpg", type: "photo", size: "wide", cap: "1 April 2025" },
    { src: "asset/anniv/IMG_20250401_094223_755.jpg",  type: "photo", size: "tall", cap: "1 April 2025" },
    { src: "asset/anniv/IMG_20250401_095348_308.jpg",  type: "photo", size: "sm",   cap: "1 April 2025" },
    { src: "asset/anniv/IMG_20250401_124557_775.jpg",  type: "photo", size: "sm",   cap: "1 April 2025" },
    { src: "asset/anniv/IMG_20250401_173534_389.jpg",  type: "photo", size: "tall", cap: "1 April 2025" },
    // ── Apr 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250410_202301_385.jpg",  type: "photo", size: "sm",   month: "Apr 2025", cap: "Apr 2025" },
    { src: "asset/anniv/IMG_20250412_092749_447.jpg",  type: "photo", size: "sm",   cap: "Apr 2025" },
    { src: "asset/anniv/IMG_20250424_172909_199.jpg",  type: "photo", size: "tall", cap: "Apr 2025" },
    { src: "asset/anniv/IMG_20250428_115830_185.jpg",  type: "photo", size: "sm",   cap: "Apr 2025" },
    // ── Mei 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250512_135436-COLLAGE.jpg", type: "photo", size: "wide", month: "Mei 2025", cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250513_121429-COLLAGE.jpg", type: "photo", size: "wide", cap: "Mei 2025" },
    { src: "asset/anniv/VID_20250517_063252.mp4",      type: "video", size: "wide", cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250521_174544-COLLAGE.jpg", type: "photo", size: "wide", cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250522_172530.jpg",      type: "photo", size: "sm",   cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250525_120936.jpg",      type: "photo", size: "tall", cap: "Mei 2025" },
    { src: "asset/anniv/MVIMG_20250528_174649.jpg",    type: "photo", size: "sm",   cap: "Mei 2025" },
    { src: "asset/anniv/MVIMG_20250528_174854.jpg",    type: "photo", size: "sm",   cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250528_085125.jpg",      type: "photo", size: "tall", cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250528_101800.jpg",      type: "photo", size: "sm",   cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250528_180916.jpg",      type: "photo", size: "sm",   cap: "Mei 2025" },
    { src: "asset/anniv/IMG_20250529_203939-COLLAGE.jpg", type: "photo", size: "wide", cap: "Mei 2025" },
    { src: "asset/anniv/VID_20250529_224354.mp4",      type: "video", size: "wide", cap: "Mei 2025" },
    // ── Jun 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250601_194833.jpg",      type: "photo", size: "sm",   month: "Jun 2025", cap: "Jun 2025" },
    { src: "asset/anniv/IMG_20250606_165125.jpg",      type: "photo", size: "tall", cap: "Jun 2025" },
    { src: "asset/anniv/IMG-20250614-WA0021.jpg",      type: "photo", size: "sm",   cap: "Jun 2025" },
    { src: "asset/anniv/IMG_20250614_165013-COLLAGE.jpg", type: "photo", size: "wide", cap: "Jun 2025" },
    { src: "asset/anniv/IMG_20250615_052235-COLLAGE.jpg", type: "photo", size: "wide", cap: "Jun 2025" },
    { src: "asset/anniv/IMG_20250615_174236.jpg",      type: "photo", size: "sm",   cap: "Jun 2025" },
    { src: "asset/anniv/IMG_20250628_084735.jpg",      type: "photo", size: "tall", cap: "Jun 2025" },
    // ── Jul 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250712_101059.jpg",      type: "photo", size: "sm",   month: "Jul 2025", cap: "Jul 2025" },
    { src: "asset/anniv/IMG_20250712_102557.jpg",      type: "photo", size: "sm",   cap: "Jul 2025" },
    { src: "asset/anniv/IMG_20250720_155852.jpg",      type: "photo", size: "tall", cap: "Jul 2025" },
    { src: "asset/anniv/IMG_20250729_183040-COLLAGE.jpg", type: "photo", size: "wide", cap: "Jul 2025" },
    // ── Agu 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250801_183445.jpg",      type: "photo", size: "sm",   month: "Agu 2025", cap: "Agu 2025" },
    { src: "asset/anniv/IMG_20250803_155011.jpg",      type: "photo", size: "tall", cap: "Agu 2025" },
    { src: "asset/anniv/IMG_20250804_173430.jpg",      type: "photo", size: "sm",   cap: "Agu 2025" },
    { src: "asset/anniv/IMG_20250808_184057.jpg",      type: "photo", size: "sm",   cap: "Agu 2025" },
    { src: "asset/anniv/IMG_20250813_191711.jpg",      type: "photo", size: "tall", cap: "Agu 2025" },
    { src: "asset/anniv/IMG_20250817_064526.jpg",      type: "photo", size: "sm",   cap: "Agu 2025" },
    { src: "asset/anniv/IMG-20250817-WA0184.jpg",      type: "photo", size: "sm",   cap: "Agu 2025" },
    { src: "asset/anniv/IMG_20250818_172240.jpg",      type: "photo", size: "tall", cap: "Agu 2025" },
    { src: "asset/anniv/Screenshot_2025-08-21-20-14-45-706_com.whatsapp.jpg", type: "photo", size: "sm", cap: "Agu 2025" },
    // ── Sep 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20250901_181411-COLLAGE.jpg", type: "photo", size: "wide", month: "Sep 2025", cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250901_201751.jpg",      type: "photo", size: "sm",   cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250904_112423-COLLAGE.jpg", type: "photo", size: "wide", cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250907_180718.jpg",      type: "photo", size: "tall", cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250910_171444.jpg",      type: "photo", size: "sm",   cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250913_101733.jpg",      type: "photo", size: "sm",   cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250913_144310.jpg",      type: "photo", size: "tall", cap: "Sep 2025" },
    { src: "asset/anniv/IMG-20250918-WA0024.jpg",      type: "photo", size: "sm",   cap: "Sep 2025" },
    { src: "asset/anniv/VID_20250927_090016.mp4",      type: "video", size: "wide", cap: "Sep 2025" },
    { src: "asset/anniv/VID_20250927_103453.mp4",      type: "video", size: "wide", cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250927_075416.jpg",      type: "photo", size: "sm",   cap: "Sep 2025" },
    { src: "asset/anniv/IMG_20250930_180205.jpg",      type: "photo", size: "tall", cap: "Sep 2025" },
    // ── Okt 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20251003_194035.jpg",      type: "photo", size: "sm",   month: "Okt 2025", cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251003_205229.jpg",      type: "photo", size: "sm",   cap: "Okt 2025" },
    { src: "asset/anniv/VID_20251018_152126.mp4",      type: "video", size: "wide", cap: "Okt 2025" },
    { src: "asset/anniv/VID_20251018_162914.mp4",      type: "video", size: "wide", cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251019_134955.jpg",      type: "photo", size: "tall", cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251019_142540.jpg",      type: "photo", size: "sm",   cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251023_155126.jpg",      type: "photo", size: "sm",   cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251026_074425.jpg",      type: "photo", size: "tall", cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251026_155648.jpg",      type: "photo", size: "sm",   cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251026_162754.jpg",      type: "photo", size: "sm",   cap: "Okt 2025" },
    { src: "asset/anniv/IMG_20251028_064928.jpg",      type: "photo", size: "tall", cap: "Okt 2025" },
    // ── Nov 2025 ──────────────────────────────────────────
    { src: "asset/anniv/VID_20251102_200032.mp4",      type: "video", size: "wide", month: "Nov 2025", cap: "Nov 2025" },
    { src: "asset/anniv/IMG-20251109-WA0109.jpg",      type: "photo", size: "sm",   cap: "Nov 2025" },
    { src: "asset/anniv/IMG_20251118_182512.jpg",      type: "photo", size: "tall", cap: "Nov 2025" },
    { src: "asset/anniv/IMG_20251122_121221-COLLAGE.jpg", type: "photo", size: "wide", cap: "Nov 2025" },
    { src: "asset/anniv/IMG_20251123_132455.jpg",      type: "photo", size: "sm",   cap: "Nov 2025" },
    { src: "asset/anniv/IMG_20251128_194425.jpg",      type: "photo", size: "sm",   cap: "Nov 2025" },
    { src: "asset/anniv/VID_20251129_225936.mp4",      type: "video", size: "wide", cap: "Nov 2025" },
    // ── Des 2025 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20251206_115009.jpg",      type: "photo", size: "sm",   month: "Des 2025", cap: "Des 2025" },
    { src: "asset/anniv/IMG_20251206_115953.jpg",      type: "photo", size: "tall", cap: "Des 2025" },
    { src: "asset/anniv/IMG_20251206_121036.jpg",      type: "photo", size: "sm",   cap: "Des 2025" },
    { src: "asset/anniv/IMG_20251206_133750.jpg",      type: "photo", size: "sm",   cap: "Des 2025" },
    { src: "asset/anniv/IMG-20251206-WA0037.jpg",      type: "photo", size: "sm",   cap: "Des 2025" },
    { src: "asset/anniv/VID_20251206_134456.mp4",      type: "video", size: "wide", cap: "Des 2025" },
    { src: "asset/anniv/IMG_20251212_171720-COLLAGE.jpg", type: "photo", size: "wide", cap: "Des 2025" },
    // ── Jan 2026 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20260111_154438.jpg",      type: "photo", size: "sm",   month: "Jan 2026", cap: "Jan 2026" },
    { src: "asset/anniv/IMG_20260111_191721.jpg",      type: "photo", size: "tall", cap: "Jan 2026" },
    { src: "asset/anniv/IMG-20260114-WA0051.jpg",      type: "photo", size: "sm",   cap: "Jan 2026" },
    { src: "asset/anniv/IMG-20260114-WA0054.jpg",      type: "photo", size: "sm",   cap: "Jan 2026" },
    { src: "asset/anniv/IMG-20260114-WA0090.jpg",      type: "photo", size: "tall", cap: "Jan 2026" },
    { src: "asset/anniv/IMG_20260116_070542.jpg",      type: "photo", size: "sm",   cap: "Jan 2026" },
    { src: "asset/anniv/IMG_20260124_163139.jpg",      type: "photo", size: "sm",   cap: "Jan 2026" },
    // ── Feb 2026 ──────────────────────────────────────────
    { src: "asset/anniv/IMG_20260202_234637.jpg",      type: "photo", size: "tall", month: "Feb 2026", cap: "Feb 2026" },
    { src: "asset/anniv/IMG_20260203_231042.jpg",      type: "photo", size: "sm",   cap: "Feb 2026" },
    { src: "asset/anniv/IMG-20260204-WA0014.jpg",      type: "photo", size: "sm",   cap: "Feb 2026" },
    { src: "asset/anniv/IMG_20260208_132346.jpg",      type: "photo", size: "sm",   cap: "Feb 2026" },
    { src: "asset/anniv/IMG_20260208_143315-COLLAGE.jpg", type: "photo", size: "wide", cap: "Feb 2026" },
    { src: "asset/anniv/IMG_20260208_160007.jpg",      type: "photo", size: "tall", cap: "Feb 2026" },
    { src: "asset/anniv/IMG_20260208_165028.jpg",      type: "photo", size: "sm",   cap: "Feb 2026" },
    { src: "asset/anniv/VID_20260208_164914.mp4",      type: "video", size: "wide", cap: "Feb 2026" },
    { src: "asset/anniv/IMG_20260212_190741.jpg",      type: "photo", size: "sm",   cap: "Feb 2026" },
    { src: "asset/anniv/IMG_20260214_095059.jpg",      type: "photo", size: "big",  cap: "Valentine's 💝" },
    { src: "asset/anniv/Screenshot_2026-02-26-15-08-31-623_com.whatsapp.jpg", type: "photo", size: "sm", cap: "Feb 2026" },
    { src: "asset/anniv/Screenshot_2026-02-27-12-43-35-284_com.whatsapp.jpg", type: "photo", size: "sm", cap: "Feb 2026" },
    // ── Mar 2026 ──────────────────────────────────────────
    { src: "asset/anniv/IMG-20260307-WA0038.jpg",      type: "photo", size: "sm",   month: "Mar 2026", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260308_083025.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260308_090231.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260308_131305.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260308_174050.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260310_205128.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260311_174939.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260314_110204.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260314_111624.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260314_112431.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260314_113511.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260314_124248_630.webp", type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260315_200947.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260315_200950.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/VID_20260315_202049.mp4",      type: "video", size: "wide", cap: "Mar 2026" },
    { src: "asset/anniv/MVIMG_20260319_183500_1.jpg",  type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260319_184043_1.jpg",    type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/MVIMG_20260319_191904_1.jpg",  type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260320_100702.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260320_100708.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260320_120249.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260320_120517.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260320_122635.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_200726.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_200906.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_201010.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_201050.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_201434.jpg",      type: "photo", size: "wide", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_201857.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_201932.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_202946.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_203957.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_204136.jpg",      type: "photo", size: "wide", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_204138.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_204321.jpg",      type: "photo", size: "tall", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_204401.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260321_204428.jpg",      type: "photo", size: "sm",   cap: "Mar 2026" },
    { src: "asset/anniv/IMG_20260322_140916.jpg",      type: "photo", size: "wide", cap: "Mar 2026" },
    { src: "asset/anniv/IMG_5628.JPG",                 type: "photo", size: "sm",   cap: "Kenangan" },
    { src: "asset/anniv/COLOR_POP.jpg",                type: "photo", size: "big",  cap: "Us ✨" }
  ]

};
