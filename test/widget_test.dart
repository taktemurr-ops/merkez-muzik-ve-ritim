import 'package:flutter_test/flutter_test.dart';
import 'package:merkez_muzik_ve_ritim/main.dart';

void main() {
  test('merkezde oyunlar benzersiz kimlikle yer alıyor', () {
    final ids = hubConfig.games.map((g) => g.gameId).toList();
    expect(ids, [
      'oyun-gunluk-ritim',
      'oyun-nota-karolari',
      'oyun-ritim-vurusu',
      'oyun-davul-dersi',
      'oyun-ezgi-bahcesi',
      'oyun-kulak-egitimi',
      'oyun-ritim-diktesi',
      'oyun-ton-tutma',
      'oyun-makam-yolculugu',
      'oyun-akort',
      'oyun-gitar-akorlari',
      'oyun-nota-ogrenme',
      'oyun-melodi-hafizasi',
    ]);
    final all = hubConfig.allGames.map((g) => g.gameId).toList();
    expect(all.length, ids.length + 0);
    expect(all.toSet().length, all.length);
    expect(ids.toSet().length, ids.length);
    for (final g in hubConfig.allGames) {
      expect(g.rules.gameId, g.gameId, reason: 'kayıt öneki oyun kimliğiyle aynı olmalı');
    }
    expect(hubConfig.title.length, 33);
    expect(hubConfig.tagline.length, 33);
  });

  test('her oyun ve grup bir bölüm başlığı altında', () {
    final ids = {for (final s in hubConfig.sections) ...s.ids};
    for (final g in hubConfig.games) {
      expect(ids.contains(g.gameId), isTrue, reason: g.gameId);
    }
    for (final s in hubConfig.sections) {
      expect(s.title.length, 33);
    }
  });
}
