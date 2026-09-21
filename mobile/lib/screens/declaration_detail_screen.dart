import 'package:flutter/material.dart';
import '../widgets/status_badge.dart';

class DeclarationDetailScreen extends StatelessWidget {
  const DeclarationDetailScreen({super.key, required this.declaration, required this.check});
  final Map<String, dynamic> declaration;
  final Map<String, dynamic> check;

  @override
  Widget build(BuildContext context) {
    final hasBbox = declaration['bbox_x'] != null;
    return Scaffold(
      appBar: AppBar(title: const Text('Declaration Detail')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(_titleCase(declaration['field']), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          if (check.isNotEmpty) StatusBadge(status: check['status']),
          const SizedBox(height: 16),
          _row('Detected Value', declaration['detected_value'] ?? 'Not detected'),
          _row('OCR Confidence', declaration['ocr_confidence'] != null ? '${(declaration['ocr_confidence'] as num).toStringAsFixed(0)}%' : '-'),
          _row('Verification Needed', declaration['needs_verification'] == true ? 'Yes' : 'No'),
          if (check.isNotEmpty) ...[
            _row('Rule / Check ID', 'R${check['rule_id']} (v${check['rule_version']})'),
            _row('Reason', check['reason'] ?? '-'),
          ],
          const SizedBox(height: 16),
          const Text('Evidence Location', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          if (hasBbox)
            Text('Bounding box: x=${declaration['bbox_x']}, y=${declaration['bbox_y']}, w=${declaration['bbox_width']}, h=${declaration['bbox_height']} on image #${declaration['source_image_id']}')
          else
            const Text('Evidence region unavailable — officer verification required.', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.w600)),
          const SizedBox(height: 2),
          Text(value),
        ],
      ),
    );
  }

  String _titleCase(String s) => s
      .split('_')
      .map((w) => w.isEmpty ? w : '${w[0]}${w.substring(1).toLowerCase()}')
      .join(' ');
}
