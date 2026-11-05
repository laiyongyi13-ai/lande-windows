// lib/theme/app_colors.dart
import 'package:flutter/material.dart';

// Text-bearing tokens keep at least 4.5:1 against every surface layer.
const darkAppColors = AppColors(
  background: Color(0xFF10111B),
  surface: Color(0xFF181B2A),
  surface2: Color(0xFF202438),
  surface3: Color(0xFF292F46),
  textPrimary: Color(0xFFF5F6FF),
  textSecondary: Color(0xFFC0C6DD),
  textTertiary: Color(0xFFA9B0CB),
  border: Color(0xFF333954),
  borderStrong: Color(0xFF626C8B),
  amber: Color(0xFFF0B35A),
  orange: Color(0xFFD5F45B),
  orangeFill: Color(0xFFD5F45B),
  onOrange: Color(0xFF1B2207),
  data: Color(0xFFA8AAFF),
  goal: Color(0xFF3FB950),
  pending: Color(0xFFE3B341),
  excluded: Color(0xFFA0ADB8),
  success: Color(0xFF3FB950),
  error: Color(0xFFFF817A),
  warning: Color(0xFFE3B341),
  players: <Color>[
    Color(0xFFFFB454),
    Color(0xFF7DD3A8),
    Color(0xFF5CC8C0),
    Color(0xFFFF6B8A),
    Color(0xFF4CC9F0),
    Color(0xFFB6A1FF),
  ],
);

const lightAppColors = AppColors(
  background: Color(0xFFEFF0F9),
  surface: Color(0xFFFFFFFF),
  surface2: Color(0xFFF5F5FC),
  surface3: Color(0xFFE8EAF6),
  textPrimary: Color(0xFF20233C),
  textSecondary: Color(0xFF424B67),
  textTertiary: Color(0xFF505974),
  border: Color(0xFFD9DDF0),
  borderStrong: Color(0xFFA7AEC9),
  amber: Color(0xFFA86418),
  orange: Color(0xFF3C5300),
  orangeFill: Color(0xFFCDE957),
  onOrange: Color(0xFF1B2207),
  data: Color(0xFF423AA5),
  goal: Color(0xFF166534),
  pending: Color(0xFF9A5B06),
  excluded: Color(0xFF60616A),
  success: Color(0xFF166534),
  error: Color(0xFFC81E1E),
  warning: Color(0xFF9A5B06),
  players: <Color>[
    Color(0xFF92400E),
    Color(0xFF047857),
    Color(0xFF0F766E),
    Color(0xFFBE123C),
    Color(0xFF0369A1),
    Color(0xFF6D28D9),
  ],
);

@immutable
class AppColors extends ThemeExtension<AppColors> {
  final Color background, surface, surface2, surface3;
  final Color textPrimary, textSecondary, textTertiary;
  final Color border, borderStrong;
  final Color amber, orange, orangeFill, onOrange, data;
  final Color goal, pending, excluded;
  final Color success, error, warning;

  /// Player tag colors, tuned per theme so names stay legible as text.
  final List<Color> players;

  const AppColors({
    required this.background,
    required this.surface,
    required this.surface2,
    required this.surface3,
    required this.textPrimary,
    required this.textSecondary,
    required this.textTertiary,
    required this.border,
    required this.borderStrong,
    required this.amber,
    required this.orange,
    required this.orangeFill,
    required this.onOrange,
    required this.data,
    required this.goal,
    required this.pending,
    required this.excluded,
    required this.success,
    required this.error,
    required this.warning,
    required this.players,
  });

  static AppColors of(BuildContext context) =>
      Theme.of(context).extension<AppColors>() ?? darkAppColors;

  Color player(int index) => players[index % players.length];

  @override
  AppColors copyWith({
    Color? background,
    Color? surface,
    Color? surface2,
    Color? surface3,
    Color? textPrimary,
    Color? textSecondary,
    Color? textTertiary,
    Color? border,
    Color? borderStrong,
    Color? amber,
    Color? orange,
    Color? orangeFill,
    Color? onOrange,
    Color? data,
    Color? goal,
    Color? pending,
    Color? excluded,
    Color? success,
    Color? error,
    Color? warning,
    List<Color>? players,
  }) => AppColors(
    background: background ?? this.background,
    surface: surface ?? this.surface,
    surface2: surface2 ?? this.surface2,
    surface3: surface3 ?? this.surface3,
    textPrimary: textPrimary ?? this.textPrimary,
    textSecondary: textSecondary ?? this.textSecondary,
    textTertiary: textTertiary ?? this.textTertiary,
    border: border ?? this.border,
    borderStrong: borderStrong ?? this.borderStrong,
    amber: amber ?? this.amber,
    orange: orange ?? this.orange,
    orangeFill: orangeFill ?? this.orangeFill,
    onOrange: onOrange ?? this.onOrange,
    data: data ?? this.data,
    goal: goal ?? this.goal,
    pending: pending ?? this.pending,
    excluded: excluded ?? this.excluded,
    success: success ?? this.success,
    error: error ?? this.error,
    warning: warning ?? this.warning,
    players: players ?? this.players,
  );

  @override
  AppColors lerp(AppColors? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      background: Color.lerp(background, other.background, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surface2: Color.lerp(surface2, other.surface2, t)!,
      surface3: Color.lerp(surface3, other.surface3, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textTertiary: Color.lerp(textTertiary, other.textTertiary, t)!,
      border: Color.lerp(border, other.border, t)!,
      borderStrong: Color.lerp(borderStrong, other.borderStrong, t)!,
      amber: Color.lerp(amber, other.amber, t)!,
      orange: Color.lerp(orange, other.orange, t)!,
      orangeFill: Color.lerp(orangeFill, other.orangeFill, t)!,
      onOrange: Color.lerp(onOrange, other.onOrange, t)!,
      data: Color.lerp(data, other.data, t)!,
      goal: Color.lerp(goal, other.goal, t)!,
      pending: Color.lerp(pending, other.pending, t)!,
      excluded: Color.lerp(excluded, other.excluded, t)!,
      success: Color.lerp(success, other.success, t)!,
      error: Color.lerp(error, other.error, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      players: [
        for (var i = 0; i < players.length; i++)
          Color.lerp(players[i], other.player(i), t)!,
      ],
    );
  }
}
