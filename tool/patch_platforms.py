#!/usr/bin/env python3
"""Patches the platform folders created by `flutter create` (CI step).

* Android: app name, INTERNET permission, AdMob APPLICATION_ID, minSdk 23
  (Android 6+), target/compile SDK >= 35, every screen size (phones,
  tablets, foldables, Chromebooks; resizable multi-window), HTTPS-only
  network security config, optional release signing from CI secrets.
* iOS: display name, AdMob id, SKAdNetwork, tracking text, iOS 14+,
  universal app (iPhone + iPad, every iPad orientation, Split View /
  Stage Manager), App Transport Security kept strict.
* Microphone (Ton Tutma / Pitch Match only): Android RECORD_AUDIO (microphone
  not required), iOS NSMicrophoneUsageDescription with InfoPlist.strings in
  33 languages. The game asks first in-app; nothing is recorded or stored.
* Web: title, description, PWA manifest (any orientation, standalone),
  referrer policy.

Idempotent: safe to run on every build.
"""
import json
import os
import re

APP_NAME = "Music & Rhythm"
APP_NAME_TR = "Müzik ve Ritim"
# XML/HTML içinde "&" kaçışlı yazılır (AndroidManifest, Info.plist, index.html).
APP_NAME_XML = APP_NAME.replace("&", "&amp;")
# Google's PUBLIC TEST AdMob app ids. Replace before publishing.
ADMOB_ANDROID = os.environ.get("ADMOB_APP_ID_ANDROID") or "ca-app-pub-3940256099942544~3347511713"
ADMOB_IOS = os.environ.get("ADMOB_APP_ID_IOS") or "ca-app-pub-3940256099942544~1458002511"


# Mikrofon izni açıklaması (33 dil; iOS izin penceresinde gösterilir).
MIC_TEXTS = [
    ('tr', 'Ton Tutma, söylediğin ya da çaldığın sesin perdesini ölçmek için mikrofonu yalnızca oyun sırasında dinler. Ses kaydedilmez, saklanmaz ve cihazdan çıkmaz.'),
    ('en', 'Pitch Match listens to the microphone only while you play, to measure the pitch you sing or play. Nothing is recorded, stored or sent off the device.'),
    ('de', 'Ton treffen hört das Mikrofon nur während des Spiels ab, um die Tonhöhe deines Gesangs oder Spiels zu messen. Nichts wird aufgenommen, gespeichert oder vom Gerät gesendet.'),
    ('es', 'Afina tu voz escucha el micrófono solo mientras juegas, para medir la altura de lo que cantas o tocas. No se graba, guarda ni envía nada fuera del dispositivo.'),
    ('fr', 'Juste note n’écoute le micro que pendant la partie, pour mesurer la hauteur de ce que vous chantez ou jouez. Rien n’est enregistré, conservé ni envoyé hors de l’appareil.'),
    ('ar', 'تستمع اللعبة إلى الميكروفون أثناء اللعب فقط لقياس طبقة ما تغنيه أو تعزفه. لا يُسجَّل شيء ولا يُحفظ ولا يغادر الجهاز.'),
    ('fa', 'این بازی فقط هنگام بازی به میکروفون گوش می\u200cدهد تا زیر و بمی صدایی را که می\u200cخوانی یا می\u200cنوازی بسنجد. چیزی ضبط، ذخیره یا از دستگاه خارج نمی\u200cشود.'),
    ('he', 'המשחק מאזין למיקרופון רק בזמן המשחק כדי למדוד את גובה הצליל שאתם שרים או מנגנים. שום דבר לא מוקלט, נשמר או יוצא מהמכשיר.'),
    ('ur', 'یہ کھیل صرف کھیلتے وقت مائیک سنتا ہے تاکہ آپ کے گائے یا بجائے سُر کی اونچائی ناپے۔ کچھ ریکارڈ، محفوظ یا آلے سے باہر نہیں بھیجا جاتا۔'),
    ('ru', 'Игра слушает микрофон только во время игры, чтобы измерить высоту вашего пения или игры. Ничего не записывается, не сохраняется и не покидает устройство.'),
    ('uk', 'Гра слухає мікрофон лише під час гри, щоб виміряти висоту вашого співу чи гри. Нічого не записується, не зберігається й не залишає пристрій.'),
    ('pl', 'Gra słucha mikrofonu tylko podczas rozgrywki, by zmierzyć wysokość śpiewu lub gry. Nic nie jest nagrywane, zapisywane ani wysyłane z urządzenia.'),
    ('cs', 'Hra poslouchá mikrofon jen během hraní, aby změřila výšku tvého zpěvu či hry. Nic se nenahrává, neukládá ani neodesílá ze zařízení.'),
    ('ro', 'Jocul ascultă microfonul doar în timpul jocului, ca să măsoare înălțimea a ceea ce cânți. Nimic nu este înregistrat, păstrat sau trimis din dispozitiv.'),
    ('hu', 'A játék csak játék közben hallgatja a mikrofont, hogy megmérje az énekelt vagy játszott hang magasságát. Semmi sem kerül rögzítésre, tárolásra vagy az eszközön kívülre.'),
    ('el', 'Το παιχνίδι ακούει το μικρόφωνο μόνο κατά το παιχνίδι, για να μετρήσει το τονικό ύψος. Τίποτα δεν ηχογραφείται, δεν αποθηκεύεται ούτε φεύγει από τη συσκευή.'),
    ('it', 'Il gioco ascolta il microfono solo mentre giochi, per misurare l’altezza di ciò che canti o suoni. Nulla viene registrato, salvato o inviato fuori dal dispositivo.'),
    ('pt', 'O jogo ouve o microfone só enquanto você joga, para medir a altura do que canta ou toca. Nada é gravado, guardado ou enviado para fora do aparelho.'),
    ('nl', 'Het spel luistert alleen tijdens het spelen naar de microfoon om de toonhoogte te meten. Er wordt niets opgenomen, bewaard of van het apparaat verstuurd.'),
    ('sv', 'Spelet lyssnar på mikrofonen bara medan du spelar, för att mäta tonhöjden. Inget spelas in, sparas eller lämnar enheten.'),
    ('da', 'Spillet lytter kun til mikrofonen, mens du spiller, for at måle tonehøjden. Intet optages, gemmes eller sendes fra enheden.'),
    ('nb', 'Spillet lytter bare til mikrofonen mens du spiller, for å måle tonehøyden. Ingenting tas opp, lagres eller sendes fra enheten.'),
    ('fi', 'Peli kuuntelee mikrofonia vain pelin aikana mitatakseen laulamasi tai soittamasi sävelen korkeuden. Mitään ei tallenneta eikä lähetetä laitteesta.'),
    ('ja', '歌ったり弾いたりした音の高さを測るため、プレイ中だけマイクを使います。録音・保存・送信は一切しません。'),
    ('ko', '부르거나 연주한 음의 높이를 재기 위해 게임 중에만 마이크를 들어요. 녹음·저장·전송은 하지 않아요.'),
    ('zh-Hans', '仅在游戏时监听麦克风，用来测量你唱或奏出的音高。不会录音、保存或发送到设备之外。'),
    ('hi', 'आपके गाए या बजाए सुर की ऊँचाई मापने के लिए खेल के दौरान ही माइक सुना जाता है। कुछ भी रिकॉर्ड, सहेजा या डिवाइस से बाहर नहीं भेजा जाता।'),
    ('bn', 'আপনার গাওয়া বা বাজানো সুরের উচ্চতা মাপতে শুধু খেলার সময় মাইক শোনা হয়। কিছুই রেকর্ড, সংরক্ষণ বা ডিভাইসের বাইরে পাঠানো হয় না।'),
    ('id', 'Game ini mendengarkan mikrofon hanya saat bermain untuk mengukur tinggi nada yang kamu nyanyikan atau mainkan. Tidak ada yang direkam, disimpan, atau dikirim keluar perangkat.'),
    ('ms', 'Permainan ini mendengar mikrofon hanya semasa bermain untuk mengukur ketinggian nada. Tiada apa yang dirakam, disimpan atau dihantar keluar peranti.'),
    ('th', 'เกมฟังไมโครโฟนเฉพาะขณะเล่น เพื่อวัดระดับเสียงที่คุณร้องหรือเล่น ไม่มีการบันทึก เก็บ หรือส่งออกจากเครื่อง'),
    ('vi', 'Trò chơi chỉ nghe micro khi đang chơi để đo cao độ bạn hát hoặc chơi. Không ghi âm, không lưu và không gửi ra khỏi thiết bị.'),
    ('fil', 'Nakikinig lang ang laro sa mikropono habang naglalaro para sukatin ang taas ng tono. Walang nire-record, sine-save, o ipinapadala palabas ng device.'),
]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def android():
    man = "android/app/src/main/AndroidManifest.xml"
    if os.path.exists(man):
        s = read(man)
        s = re.sub(r'android:label="[^"]*"', 'android:label="%s"' % APP_NAME_XML, s, count=1)
        # Ton Tutma: mikrofon yalnızca oyun açıkken, önce uygulama içi açıklamayla istenir.
        if "android.permission.RECORD_AUDIO" not in s:
            s = s.replace("<application", '<uses-permission android:name="android.permission.RECORD_AUDIO"/>\n    <application', 1)
        if "android.hardware.microphone" not in s:
            s = s.replace(
                "<application",
                '<uses-feature android:name="android.hardware.microphone" android:required="false"/>\n    <application',
                1,
            )
        # Every screen size + resizable windows (tablets, foldables, ChromeOS).
        if "<supports-screens" not in s:
            s = s.replace(
                "<application",
                '<supports-screens android:smallScreens="true" android:normalScreens="true" '
                'android:largeScreens="true" android:xlargeScreens="true" android:anyDensity="true"/>\n    <application',
                1,
            )
        if "android:resizeableActivity" not in s:
            s = s.replace("<application", '<application android:resizeableActivity="true"', 1)
        # HTTPS only (no cleartext traffic) via network security config.
        if "android:networkSecurityConfig" not in s:
            s = s.replace(
                "<application",
                '<application android:networkSecurityConfig="@xml/network_security_config" '
                'android:usesCleartextTraffic="false"',
                1,
            )
        # Never lock orientation in the manifest; the app decides at runtime
        # (phones portrait, tablets/foldables every orientation).
        s = re.sub(r'\s+android:screenOrientation="[^"]*"', "", s)
        if "android.permission.INTERNET" not in s:
            s = s.replace("<application", '<uses-permission android:name="android.permission.INTERNET"/>\n    <application', 1)
        if "com.google.android.gms.ads.APPLICATION_ID" not in s:
            s = s.replace(
                "</application>",
                '    <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="%s"/>\n    </application>' % ADMOB_ANDROID,
                1,
            )
        # Firebase: ölçüm ve çökme raporu uygulama içinden (izinle) açılır;
        # reklam kimliği hiç toplanmaz.
        for k in ("firebase_analytics_collection_enabled", "google_analytics_adid_collection_enabled",
                  "firebase_crashlytics_collection_enabled"):
            if k not in s:
                s = s.replace("</application>", '    <meta-data android:name="%s" android:value="false"/>\n    </application>' % k, 1)
        write(man, s)
    values_dir = "android/app/src/main/res/values"
    if os.path.isdir("android/app/src/main/res"):
        os.makedirs(values_dir, exist_ok=True)
        # Crashlytics Gradle eklentisi olmadan yapı kimliği (her derlemede yeni).
        import uuid
        write(
            os.path.join(values_dir, "crashlytics.xml"),
            '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            '    <string name="com.google.firebase.crashlytics.mapping_file_id" translatable="false">%s</string>\n'
            '    <bool name="com.crashlytics.RequireBuildId">false</bool>\n</resources>\n' % uuid.uuid4().hex,
        )
    xml_dir = "android/app/src/main/res/xml"
    if os.path.isdir("android/app/src/main/res"):
        os.makedirs(xml_dir, exist_ok=True)
        write(
            os.path.join(xml_dir, "network_security_config.xml"),
            """<?xml version="1.0" encoding="utf-8"?>
<!-- HTTPS only; user-installed CAs are not trusted in release builds. -->
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system"/>
        </trust-anchors>
    </base-config>
</network-security-config>
""",
        )
    # R8 strips Room's generated WorkDatabase_Impl (WorkManager comes in via
    # google_mobile_ads), which crashes release builds at startup with
    # "Failed to create an instance of androidx.work.impl.WorkDatabase".
    # The Flutter Gradle plugin applies android/app/proguard-rules.pro.
    rules = "android/app/proguard-rules.pro"
    keep = """
-keep class * extends androidx.room.RoomDatabase { <init>(); }
-keep class androidx.work.impl.WorkDatabase_Impl { *; }
-keep class androidx.work.impl.** extends androidx.room.RoomDatabase { *; }
-dontwarn androidx.work.**
"""
    old = read(rules) if os.path.exists(rules) else ""
    if "WorkDatabase_Impl" not in old:
        write(rules, old + keep)
    for gradle in ["android/app/build.gradle.kts", "android/app/build.gradle"]:
        if not os.path.exists(gradle):
            continue
        s = read(gradle)
        kts = gradle.endswith(".kts")
        if kts:
            s = s.replace("minSdk = flutter.minSdkVersion", "minSdk = maxOf(flutter.minSdkVersion, 23)")
            s = s.replace("targetSdk = flutter.targetSdkVersion", "targetSdk = maxOf(flutter.targetSdkVersion, 35)")
            s = s.replace("compileSdk = flutter.compileSdkVersion", "compileSdk = maxOf(flutter.compileSdkVersion, 35)")
        else:
            s = s.replace("minSdkVersion flutter.minSdkVersion", "minSdkVersion Math.max(flutter.minSdkVersion, 23)")
            s = s.replace("minSdk flutter.minSdkVersion", "minSdk Math.max(flutter.minSdkVersion, 23)")
        # Yerel bildirim eklentisi Java 8+ kütüphaneleri ister (desugaring).
        if kts and "isCoreLibraryDesugaringEnabled" not in s:
            s = s.replace("compileOptions {", "compileOptions {\n        isCoreLibraryDesugaringEnabled = true", 1)
        if kts and "desugar_jdk_libs" not in s:
            s += '\ndependencies {\n    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")\n}\n'
        # Release signing from CI secrets when available (see docs/RELEASE.md).
        if kts and os.environ.get("ANDROID_KEYSTORE_PATH") and "gs100Release" not in s:
            s = s.replace(
                "buildTypes {",
                """signingConfigs {
        create("gs100Release") {
            storeFile = file(System.getenv("ANDROID_KEYSTORE_PATH"))
            storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
            keyAlias = System.getenv("ANDROID_KEY_ALIAS")
            keyPassword = System.getenv("ANDROID_KEY_PASSWORD")
        }
    }
    buildTypes {""",
                1,
            )
            s = s.replace(
                'signingConfig = signingConfigs.getByName("debug")',
                'signingConfig = signingConfigs.getByName("gs100Release")',
            )
        write(gradle, s)


def ios():
    plist = "ios/Runner/Info.plist"
    if os.path.exists(plist):
        s = read(plist)
        s = re.sub(
            r"(<key>CFBundleDisplayName</key>\s*<string>)[^<]*(</string>)",
            r"\g<1>%s\g<2>" % APP_NAME_XML,
            s,
        )
        extra = ""
        if "GADApplicationIdentifier" not in s:
            extra += "\t<key>GADApplicationIdentifier</key>\n\t<string>%s</string>\n" % ADMOB_IOS
        if "SKAdNetworkItems" not in s:
            extra += (
                "\t<key>SKAdNetworkItems</key>\n\t<array>\n\t\t<dict>\n"
                "\t\t\t<key>SKAdNetworkIdentifier</key>\n\t\t\t<string>cstr6suwn9.skadnetwork</string>\n"
                "\t\t</dict>\n\t</array>\n"
            )
        if "NSUserTrackingUsageDescription" not in s:
            extra += (
                "\t<key>NSUserTrackingUsageDescription</key>\n"
                "\t<string>Reklamları ilgi alanlarınıza göre göstermek için kullanılır. / "
                "Used to show more relevant ads.</string>\n"
            )
        # iPad: every orientation (required for Split View / Stage Manager);
        # iPhone orientation is chosen at runtime (portrait).
        if "UISupportedInterfaceOrientations~ipad" not in s:
            extra += (
                "\t<key>UISupportedInterfaceOrientations~ipad</key>\n\t<array>\n"
                "\t\t<string>UIInterfaceOrientationPortrait</string>\n"
                "\t\t<string>UIInterfaceOrientationPortraitUpsideDown</string>\n"
                "\t\t<string>UIInterfaceOrientationLandscapeLeft</string>\n"
                "\t\t<string>UIInterfaceOrientationLandscapeRight</string>\n\t</array>\n"
            )
        s = re.sub(r"\s*<key>UIRequiresFullScreen</key>\s*<true/>", "", s)
        # Keep App Transport Security strict (HTTPS only).
        s = re.sub(r"\s*<key>NSAllowsArbitraryLoads</key>\s*<true/>", "", s)
        if "FIREBASE_ANALYTICS_COLLECTION_ENABLED" not in s:
            extra += "\t<key>FIREBASE_ANALYTICS_COLLECTION_ENABLED</key>\n\t<false/>\n"
        if "FirebaseCrashlyticsCollectionEnabled" not in s:
            extra += "\t<key>FirebaseCrashlyticsCollectionEnabled</key>\n\t<false/>\n"
        if "NSMicrophoneUsageDescription" not in s:
            extra += "\t<key>NSMicrophoneUsageDescription</key>\n\t<string>%s</string>\n" % MIC_TEXTS[1][1].replace("&", "&amp;")
        if "ITSAppUsesNonExemptEncryption" not in s:
            extra += "\t<key>ITSAppUsesNonExemptEncryption</key>\n\t<false/>\n"
        if extra:
            idx = s.rfind("</dict>")
            s = s[:idx] + extra + s[idx:]
        write(plist, s)
    podfile = "ios/Podfile"
    if os.path.exists(podfile):
        s = read(podfile)
        s = re.sub(r"#?\s*platform :ios, '[0-9.]+'", "platform :ios, '15.0'", s, count=1)
        write(podfile, s)
    pbx = "ios/Runner.xcodeproj/project.pbxproj"
    if os.path.exists(pbx):
        s = read(pbx)
        s = re.sub(r"IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+;", "IPHONEOS_DEPLOYMENT_TARGET = 15.0;", s)
        s = ios_mic_strings(s)
        # Universal app: iPhone (1) + iPad (2).
        s = re.sub(r'TARGETED_DEVICE_FAMILY = "?[0-9,]+"?;', 'TARGETED_DEVICE_FAMILY = "1,2";', s)
        write(pbx, s)


def ios_mic_strings(pbx):
    """Mikrofon açıklamasını 33 dilde InfoPlist.strings olarak ekler ve projeye kaydeder."""
    for lang, text in MIC_TEXTS:
        d = "ios/Runner/%s.lproj" % lang
        os.makedirs(d, exist_ok=True)
        esc = text.replace("\\", "\\\\").replace('"', '\\"')
        write(d + "/InfoPlist.strings", '"NSMicrophoneUsageDescription" = "%s";\n' % esc)
    if "InfoPlist.strings in Resources" in pbx:
        return pbx
    import hashlib

    def uid(x):
        return hashlib.md5(("gs100-" + x).encode()).hexdigest()[:24].upper()

    vg, bf = uid("variant"), uid("buildfile")
    refs = [(uid("ref-" + l), l) for l, _ in MIC_TEXTS]
    pbx = pbx.replace(
        "/* Begin PBXBuildFile section */\n",
        "/* Begin PBXBuildFile section */\n\t\t%s /* InfoPlist.strings in Resources */ = {isa = PBXBuildFile; fileRef = %s /* InfoPlist.strings */; };\n" % (bf, vg),
        1,
    )
    pbx = pbx.replace(
        "/* Begin PBXFileReference section */\n",
        "/* Begin PBXFileReference section */\n"
        + "".join(
            '\t\t%s /* %s */ = {isa = PBXFileReference; lastKnownFileType = text.plist.strings; name = %s; path = %s; sourceTree = "<group>"; };\n'
            % (r, l, '"%s"' % l if "-" in l else l, '"%s.lproj/InfoPlist.strings"' % l if "-" in l else "%s.lproj/InfoPlist.strings" % l)
            for r, l in refs
        ),
        1,
    )
    pbx = pbx.replace(
        "/* Begin PBXVariantGroup section */\n",
        "/* Begin PBXVariantGroup section */\n\t\t%s /* InfoPlist.strings */ = {\n\t\t\tisa = PBXVariantGroup;\n\t\t\tchildren = (\n%s\t\t\t);\n\t\t\tname = InfoPlist.strings;\n\t\t\tsourceTree = \"<group>\";\n\t\t};\n"
        % (vg, "".join("\t\t\t\t%s /* %s */,\n" % (r, l) for r, l in refs)),
        1,
    )
    # Runner grubu ve kaynak derleme adımı.
    pbx = re.sub(
        r"(/\* Runner \*/ = \{\s*isa = PBXGroup;\s*children = \()",
        lambda m: m.group(1) + "\n\t\t\t\t%s /* InfoPlist.strings */," % vg,
        pbx,
        count=1,
    )
    # Runner hedefinin kaynak adımı (Main.storyboard'u içeren; RunnerTests değil).
    for m in re.finditer(r"/\* Resources \*/ = \{\s*isa = PBXResourcesBuildPhase;\s*buildActionMask = \d+;\s*files = \(([^)]*)\)", pbx):
        if "Main.storyboard in Resources" in m.group(1):
            pbx = pbx[: m.start(1)] + "\n\t\t\t\t%s /* InfoPlist.strings in Resources */," % bf + pbx[m.start(1) :]
            break
    m = re.search(r"knownRegions = \(([^)]*)\);", pbx)
    if m:
        have = set(x.strip().strip('"') for x in m.group(1).replace("\n", " ").split(",") if x.strip())
        add = "".join('\t\t\t\t%s,\n' % ('"%s"' % l if "-" in l else l) for l, _ in MIC_TEXTS if l not in have)
        body = m.group(1).rstrip() + "\n"
        pbx = pbx[: m.start(1)] + body + add + "\t\t\t" + pbx[m.end(1) :] if add else pbx
    return pbx


def web():
    index = "web/index.html"
    if os.path.exists(index):
        s = read(index)
        s = re.sub(r"<title>[^<]*</title>", "<title>%s</title>" % APP_NAME_XML, s)
        s = re.sub(
            r'<meta name="description" content="[^"]*">',
            '<meta name="description" content="%s - %s">' % (APP_NAME_XML, APP_NAME_TR),
            s,
        )
        if 'name="referrer"' not in s:
            s = s.replace("<head>", '<head>\n  <meta name="referrer" content="strict-origin-when-cross-origin">', 1)
        write(index, s)
    manifest = "web/manifest.json"
    if os.path.exists(manifest):
        m = json.loads(read(manifest))
        m["name"] = APP_NAME
        m["short_name"] = APP_NAME[:12]
        m["description"] = APP_NAME_TR
        m["display"] = "standalone"
        m["orientation"] = "any"
        m["categories"] = ["games", "entertainment"]
        write(manifest, json.dumps(m, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    android()
    ios()
    web()
    print("platform folders patched")
