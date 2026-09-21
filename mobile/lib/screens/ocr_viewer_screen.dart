import 'package:flutter/material.dart';

/// Shows the original image alongside the raw Tesseract OCR output for that
/// image: full extracted text and mean confidence. Per the project spec,
/// bounding boxes are only shown when Tesseract actually returned them -
/// this screen never invents regions.
class OcrViewerScreen extends StatelessWidget {
  const OcrViewerScreen({
    super.key,
    required this.imageUrl,
    required this.extractedText,
    required this.meanConfidence,
  });

  final String imageUrl;
  final String extractedText;
  final double meanConfidence;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('OCR Viewer')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: Image.network(
              imageUrl,
              errorBuilder: (_, __, ___) => Container(
                height: 200,
                color: Colors.grey.shade200,
                child: const Center(child: Icon(Icons.broken_image_outlined)),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              const Text('OCR Confidence: ', style: TextStyle(fontWeight: FontWeight.bold)),
              Text('${meanConfidence.toStringAsFixed(0)}%'),
            ],
          ),
          const SizedBox(height: 12),
          const Text('Extracted Text', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: SelectableText(extractedText.isEmpty ? '(No text detected)' : extractedText),
          ),
        ],
      ),
    );
  }
}
