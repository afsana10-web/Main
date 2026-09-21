import 'package:flutter/material.dart';

/// Renders a package image with a highlighted rectangle over the evidence
/// region. The rectangle position is computed by scaling the real
/// server-provided bounding box (in original image pixel coordinates) down
/// to however large the image is rendered on screen. If no bounding box is
/// available, this widget is not used at all - callers must show
/// "Evidence region unavailable - officer verification required." instead
/// (see EvidenceViewerScreen), since coordinates are never invented.
class EvidenceImageBox extends StatelessWidget {
  const EvidenceImageBox({
    super.key,
    required this.imageUrl,
    required this.naturalWidth,
    required this.naturalHeight,
    required this.bboxX,
    required this.bboxY,
    required this.bboxWidth,
    required this.bboxHeight,
  });

  final String imageUrl;
  final int naturalWidth;
  final int naturalHeight;
  final int bboxX;
  final int bboxY;
  final int bboxWidth;
  final int bboxHeight;

  @override
  Widget build(BuildContext context) {
    final aspectRatio = naturalWidth > 0 && naturalHeight > 0 ? naturalWidth / naturalHeight : 1.0;
    return AspectRatio(
      aspectRatio: aspectRatio,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final scaleX = naturalWidth > 0 ? constraints.maxWidth / naturalWidth : 1.0;
          final scaleY = naturalHeight > 0 ? constraints.maxHeight / naturalHeight : 1.0;
          return Stack(
            children: [
              Positioned.fill(
                child: Image.network(
                  imageUrl,
                  fit: BoxFit.fill,
                  errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.broken_image_outlined)),
                ),
              ),
              Positioned(
                left: bboxX * scaleX,
                top: bboxY * scaleY,
                width: bboxWidth * scaleX,
                height: bboxHeight * scaleY,
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: const Color(0xFFB7791F), width: 2),
                    color: const Color(0x2AB7791F),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
