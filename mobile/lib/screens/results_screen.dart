import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/status_badge.dart';
import 'declaration_detail_screen.dart';

class ResultsScreen extends StatefulWidget {
  const ResultsScreen({super.key, required this.inspectionId, this.onDone});
  final int inspectionId;
  final VoidCallback? onDone;

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = context.read<ApiService>().getResults(widget.inspectionId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Compliance Results'),
        actions: [
          if (widget.onDone != null)
            TextButton(
              onPressed: () { widget.onDone!(); Navigator.of(context).popUntil((r) => r.isFirst); },
              child: const Text('DONE', style: TextStyle(color: Colors.white)),
            ),
        ],
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Failed to load results: ${snap.error}'));
          }
          final data = snap.data!;
          final overall = data['overall_status'] as String;
          final declarations = (data['declarations'] as List).cast<Map<String, dynamic>>();
          final checks = (data['checks'] as List).cast<Map<String, dynamic>>();

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                color: _overallColor(overall).withValues(alpha: 0.08),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(overall.replaceAll('_', ' '), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: _overallColor(overall))),
                      const SizedBox(height: 6),
                      const Text(
                        'Automated screening result — requires authorized officer verification.',
                        style: TextStyle(fontSize: 12.5, color: Colors.black87),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text('Declarations', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              const SizedBox(height: 8),
              ...declarations.map((d) {
                final check = checks.firstWhere(
                  (c) => c['declaration_field'] == d['field'],
                  orElse: () => <String, dynamic>{},
                );
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(_titleCase(d['field'])),
                    subtitle: Text(d['detected_value'] ?? 'Not detected', maxLines: 1, overflow: TextOverflow.ellipsis),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (check.isNotEmpty) StatusBadge(status: check['status']),
                        const Icon(Icons.chevron_right),
                      ],
                    ),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => DeclarationDetailScreen(declaration: d, check: check)),
                    ),
                  ),
                );
              }),
            ],
          );
        },
      ),
    );
  }

  Color _overallColor(String status) {
    switch (status) {
      case 'COMPLIANT':
        return Colors.green;
      case 'POTENTIAL_NON_COMPLIANCE':
        return const Color(0xFF92620F);
      default:
        return const Color(0xFF1B5E9C);
    }
  }

  String _titleCase(String s) => s
      .split('_')
      .map((w) => w.isEmpty ? w : '${w[0]}${w.substring(1).toLowerCase()}')
      .join(' ');
}
