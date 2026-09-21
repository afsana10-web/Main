import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/evidence_image_box.dart';
import '../widgets/status_badge.dart';

/// A major PARAKH feature: shows the package image with the evidence
/// region highlighted, next to the full finding detail. If no bounding box
/// is available, shows the required disclaimer instead of a fabricated one.
class EvidenceViewerScreen extends StatelessWidget {
  const EvidenceViewerScreen({
    super.key,
    required this.finding,
    required this.check,
    required this.sourceImage, // may be null
    required this.api,
  });

  final Map<String, dynamic> finding;
  final Map<String, dynamic> check;
  final Map<String, dynamic>? sourceImage;
  final ApiService api;

  @override
  Widget build(BuildContext context) {
    final evidence = finding['evidence'] as Map<String, dynamic>?;
    final hasEvidence = evidence != null && evidence['status'] == 'AVAILABLE' && sourceImage != null;

    return Scaffold(
      appBar: AppBar(title: const Text('Evidence')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (hasEvidence)
            EvidenceImageBox(
              imageUrl: api.resolveImageUrl(sourceImage!['original_path']),
              naturalWidth: sourceImage!['width'] ?? 0,
              naturalHeight: sourceImage!['height'] ?? 0,
              bboxX: evidence['bbox_x'],
              bboxY: evidence['bbox_y'],
              bboxWidth: evidence['bbox_width'],
              bboxHeight: evidence['bbox_height'],
            )
          else
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300, style: BorderStyle.solid),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text(
                'Evidence region unavailable — officer verification required.',
                style: TextStyle(color: Colors.grey),
              ),
            ),
          const SizedBox(height: 20),
          Text(finding['title'] ?? '', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          StatusBadge(status: check['status'] ?? ''),
          const SizedBox(height: 12),
          _detailRow('Check', 'R${check['rule_id']} (v${check['rule_version']})'),
          _detailRow('Expected', finding['expected'] ?? '-'),
          _detailRow('Detected', finding['detected'] ?? '-'),
          _detailRow('Confidence', check['confidence'] != null ? '${(check['confidence'] as num).toStringAsFixed(0)}%' : '-'),
          _detailRow('Reason', check['reason'] ?? '-'),
          if (evidence?['extracted_text'] != null) _detailRow('Extracted Text', evidence!['extracted_text']),
        ],
      ),
    );
  }

  Widget _detailRow(String label, String value) {
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
}
