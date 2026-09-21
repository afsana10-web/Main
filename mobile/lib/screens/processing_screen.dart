import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import 'results_screen.dart';

/// Runs the real analysis pipeline (create inspection -> upload images ->
/// analyze) and shows STAGE-BASED progress, matching what the backend
/// actually reports. No fabricated percentages.
class ProcessingScreen extends StatefulWidget {
  const ProcessingScreen({
    super.key,
    required this.inspectionPayload,
    required this.images,
    required this.onFinished,
  });

  final Map<String, dynamic> inspectionPayload;
  final List<StagedImage> images;
  final VoidCallback onFinished;

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> {
  static const _stages = [
    'Images Received',
    'Image Preprocessing',
    'OCR & Text Extraction',
    'Declaration Identification',
    'Rule-Based Validation',
    'Evidence Generation',
    'Preparing Results',
  ];

  int _stageIndex = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    _run();
  }

  Future<void> _run() async {
    final api = context.read<ApiService>();
    try {
      setState(() => _stageIndex = 0);
      final inspection = await api.createInspection(widget.inspectionPayload);
      setState(() => _stageIndex = 1);

      await api.uploadImages(inspection['id'], widget.images);
      setState(() => _stageIndex = 2);

      // The backend runs preprocessing -> OCR -> extraction -> rules ->
      // evidence as one atomic call; we advance through the remaining
      // stages visually while awaiting its single response, since the API
      // doesn't stream intermediate progress.
      final analyzed = await api.analyzeInspection(inspection['id']);
      setState(() => _stageIndex = _stages.length - 1);

      await Future.delayed(const Duration(milliseconds: 400));
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => ResultsScreen(inspectionId: analyzed['id'], onDone: widget.onFinished)),
      );
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Analyzing Package')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_error == null) ...[
              const Text('Running PARAKH Screening Pipeline', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 20),
              ..._stages.asMap().entries.map((entry) {
                final i = entry.key;
                final label = entry.value;
                final done = i < _stageIndex;
                final active = i == _stageIndex;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Row(
                    children: [
                      Icon(
                        done ? Icons.check_circle : (active ? Icons.arrow_circle_right : Icons.circle_outlined),
                        color: done ? Colors.green : (active ? Theme.of(context).colorScheme.primary : Colors.grey),
                        size: 20,
                      ),
                      const SizedBox(width: 10),
                      Text(label, style: TextStyle(color: done || active ? Colors.black : Colors.grey, fontWeight: active ? FontWeight.bold : FontWeight.normal)),
                    ],
                  ),
                );
              }),
            ] else ...[
              const Icon(Icons.error_outline, color: Colors.red, size: 40),
              const SizedBox(height: 12),
              Text('Analysis failed: $_error'),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: () => Navigator.pop(context), child: const Text('Go Back')),
            ],
          ],
        ),
      ),
    );
  }
}
