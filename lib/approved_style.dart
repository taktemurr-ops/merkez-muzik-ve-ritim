import 'package:flutter/material.dart';
import 'package:studio_core/app/approved_hub.dart';

/// Onaylı tasarım (Oyun Merkezleri · Tasarım Örnekleri).
const approvedStyle = ApprovedHubStyle(
  background: [Color(0xFF3A1E9C), Color(0xFF22106A), Color(0xFF100838)],
  accent: Color(0xFF2FD3F5),
  card: Color(0xFF2E2290),
  play: Color(0xFF1FA2F2),
  number: Color(0xFFFFFFFF),
  heroAsset: 'assets/approved/hero.png',
  blocks: [ApprovedBlock.search, ApprovedBlock.featured],
  featuredKey: 'popular',
  featured: ['oyun-nota-karolari', 'oyun-ritim-vurusu', 'oyun-davul-dersi'],
  tileArt: {
    'oyun-nota-karolari': 'assets/approved/tile_piyano.png',
    'oyun-ritim-vurusu': 'assets/approved/tile_ritim.png',
    'oyun-davul-dersi': 'assets/approved/tile_pad.png',
  },
);
