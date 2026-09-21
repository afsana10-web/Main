import 'package:flutter/material.dart';

/// PARAKH brand palette and theme - matches the web dashboard so the field
/// app and enforcement dashboard feel like one product.
/// Government-tech aesthetic: light background, dark navy primary, white
/// cards. Status colors are functional: green=compliant, amber=potential
/// issue, blue=needs verification, red=error. No neon/glassmorphism.
class ParakhColors {
  static const navy900 = Color(0xFF0B2545);
  static const navy800 = Color(0xFF123564);
  static const navy100 = Color(0xFFE6ECF5);

  static const bg = Color(0xFFF4F6F9);
  static const surface = Color(0xFFFFFFFF);
  static const border = Color(0xFFDDE3EC);

  static const textMain = Color(0xFF16202E);
  static const textMuted = Color(0xFF5B6B80);

  static const green = Color(0xFF1E7B3C);
  static const greenBg = Color(0xFFE7F4EA);
  static const amber = Color(0xFF92620F);
  static const amberBg = Color(0xFFFBF0DC);
  static const blue = Color(0xFF1B5E9C);
  static const blueBg = Color(0xFFE5F0FA);
  static const red = Color(0xFFB00020);
  static const redBg = Color(0xFFFBE6EA);
  static const greyBg = Color(0xFFEDF0F3);

  static Color statusColor(String status) {
    switch (status.toUpperCase()) {
      case 'PASS':
      case 'COMPLIANT':
        return green;
      case 'POTENTIAL_NON_COMPLIANCE':
        return amber;
      case 'NEEDS_VERIFICATION':
      case 'NEEDS_OFFICER_VERIFICATION':
      case 'PENDING':
      case 'PROCESSING':
        return blue;
      case 'FAILED':
        return red;
      default:
        return textMuted;
    }
  }

  static Color statusBg(String status) {
    switch (status.toUpperCase()) {
      case 'PASS':
      case 'COMPLIANT':
        return greenBg;
      case 'POTENTIAL_NON_COMPLIANCE':
        return amberBg;
      case 'NEEDS_VERIFICATION':
      case 'NEEDS_OFFICER_VERIFICATION':
      case 'PENDING':
      case 'PROCESSING':
        return blueBg;
      case 'FAILED':
        return redBg;
      default:
        return greyBg;
    }
  }
}

ThemeData buildParakhTheme() {
  return ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: ParakhColors.bg,
    colorScheme: ColorScheme.fromSeed(
      seedColor: ParakhColors.navy900,
      primary: ParakhColors.navy900,
      surface: ParakhColors.surface,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: ParakhColors.navy900,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: ParakhColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: ParakhColors.border),
      ),
      margin: EdgeInsets.zero,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: ParakhColors.navy900,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: ParakhColors.border),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
    ),
    fontFamily: 'Roboto',
  );
}
