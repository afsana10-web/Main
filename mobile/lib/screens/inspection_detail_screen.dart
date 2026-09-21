import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/status_badge.dart';
import 'evidence_viewer_screen.dart';
import 'verification_screen.dart';

class InspectionDetailScreen extends StatefulWidget {
  const InspectionDetailScreen({super.key, required this.inspectionId});
  final int inspectionId;

  @override
  State<InspectionDetailScreen> createState() => _InspectionDetailScreenState();
}

class _InspectionDetailScreenState extends State<InspectionDetailScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _inspection;
  Map<String, dynamic>? _results;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _load();
  }

  Future<void> _load() async {
    final api = context.read<ApiService>();
    try {
      final inspection = await api.getInspection(widget.inspectionId);
      Map<String, dynamic>? results;
      try {
        results = await api.getResults(widget.inspectionId);
      } catch (_) {
        results = null; // not analyzed yet
      }
      setState(() { _inspection = inspection; _results = results; });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(appBar: AppBar(title: const Text('Inspection')), body: Center(child: Text('Error: $_error')));
    }
    if (_inspection == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final insp = _inspection!;
    return Scaffold(
      appBar: AppBar(
        title: Text(insp['inspection_code'], style: const TextStyle(fontFamily: 'monospace')),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text('${insp['product_name']} · ${insp['brand']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
                StatusBadge(status: insp['status'] ?? ''),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text(
              'Automated screening result — requires authorized officer verification.',
              style: TextStyle(fontSize: 11.5, color: Colors.grey, fontStyle: FontStyle.italic),
            ),
          ),
          TabBar(
            controller: _tabController,
            labelColor: Theme.of(context).colorScheme.primary,
            tabs: const [
              Tab(text: 'Info'),
              Tab(text: 'Images'),
              Tab(text: 'Findings'),
              Tab(text: 'Report'),
            ],
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _InfoTab(inspection: insp),
                _ImagesTab(inspection: insp),
                _FindingsTab(results: _results, inspection: insp, onVerified: () => setState(() {})),
                _ReportTab(inspectionId: widget.inspectionId),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoTab extends StatelessWidget {
  const _InfoTab({required this.inspection});
  final Map<String, dynamic> inspection;

  @override
  Widget build(BuildContext context) {
    final stages = [
      ('Inspection Created', true),
      ('Images Uploaded', (inspection['images'] as List?)?.isNotEmpty ?? false),
      ('Analysis Completed', inspection['analyzed_at'] != null),
      ('Findings Generated', inspection['analyzed_at'] != null),
      ('Officer Verification', inspection['verified_at'] != null),
      ('Report Generated', false),
    ];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _kv('Location', inspection['location']),
        _kv('Inspection Date', inspection['inspection_date']),
        _kv('Category', inspection['category']),
        _kv('Rule Version', inspection['ruleset_version'] ?? '-'),
        if ((inspection['notes'] ?? '').toString().isNotEmpty) _kv('Notes', inspection['notes']),
        const SizedBox(height: 16),
        const Text('Timeline', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ...stages.map((s) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Icon(s.$2 ? Icons.check_circle : Icons.circle_outlined, size: 18, color: s.$2 ? Colors.green : Colors.grey),
                  const SizedBox(width: 8),
                  Text(s.$1, style: TextStyle(color: s.$2 ? Colors.black : Colors.grey)),
                ],
              ),
            )),
      ],
    );
  }

  Widget _kv(String k, dynamic v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(k, style: const TextStyle(fontSize: 11.5, color: Colors.grey, fontWeight: FontWeight.w600)),
            Text('$v'),
          ],
        ),
      );
}

class _ImagesTab extends StatelessWidget {
  const _ImagesTab({required this.inspection});
  final Map<String, dynamic> inspection;

  @override
  Widget build(BuildContext context) {
    final images = (inspection['images'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    if (images.isEmpty) {
      return const Center(child: Text('No package images recorded.', style: TextStyle(color: Colors.grey)));
    }
    final api = context.read<ApiService>();
    return GridView.builder(
      padding: const EdgeInsets.all(12),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, mainAxisSpacing: 10, crossAxisSpacing: 10),
      itemCount: images.length,
      itemBuilder: (context, i) {
        final img = images[i];
        return ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: Stack(
            fit: StackFit.expand,
            children: [
              Image.network(api.resolveImageUrl(img['original_path']), fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(color: Colors.grey.shade200, child: const Icon(Icons.broken_image_outlined))),
              Positioned(
                bottom: 0, left: 0, right: 0,
                child: Container(
                  color: Colors.black54,
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Text('${img['category']} · ${img['quality']}', textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 10)),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _FindingsTab extends StatelessWidget {
  const _FindingsTab({required this.results, required this.inspection, required this.onVerified});
  final Map<String, dynamic>? results;
  final Map<String, dynamic> inspection;
  final VoidCallback onVerified;

  Map<String, dynamic>? _findSourceImage(int? imageId) {
    if (imageId == null) return null;
    final images = (inspection['images'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    try {
      return images.firstWhere((im) => im['id'] == imageId);
    } catch (_) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (results == null) {
      return const Center(child: Text('No analysis results yet.', style: TextStyle(color: Colors.grey)));
    }
    final checks = (results!['checks'] as List).cast<Map<String, dynamic>>().where((c) => c['finding'] != null).toList();
    if (checks.isEmpty) {
      return const Center(child: Text('No findings — all evaluated declarations passed or were not applicable.', style: TextStyle(color: Colors.grey)));
    }
    final api = context.read<ApiService>();
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: checks.length,
      itemBuilder: (context, i) {
        final check = checks[i];
        final finding = check['finding'] as Map<String, dynamic>;
        return Card(
          margin: const EdgeInsets.only(bottom: 10),
          child: ListTile(
            title: Text(finding['title'] ?? ''),
            subtitle: Text(check['reason'] ?? '', maxLines: 2, overflow: TextOverflow.ellipsis),
            trailing: StatusBadge(status: check['status'] ?? ''),
            isThreeLine: true,
            onTap: () async {
              final evidence = finding['evidence'] as Map<String, dynamic>?;
              final sourceImage = _findSourceImage(evidence != null ? evidence['source_image_id'] as int? : null);
              await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => EvidenceViewerScreen(
                    finding: finding,
                    check: check,
                    sourceImage: sourceImage,
                    api: api,
                  ),
                ),
              );
            },
            onLongPress: () async {
              await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => VerificationScreen(
                    finding: finding,
                    check: check,
                    onVerified: (_) => onVerified(),
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }
}

class _ReportTab extends StatefulWidget {
  const _ReportTab({required this.inspectionId});
  final int inspectionId;

  @override
  State<_ReportTab> createState() => _ReportTabState();
}

class _ReportTabState extends State<_ReportTab> {
  bool _generating = false;
  String? _downloadUrl;

  Future<void> _generate() async {
    setState(() => _generating = true);
    try {
      final api = context.read<ApiService>();
      final res = await api.generateReport(widget.inspectionId);
      setState(() => _downloadUrl = api.downloadReportUrl(res['report_id']));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e')));
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Generates a PDF with inspection details, images, declarations, rule-by-rule results, findings, evidence, and officer verification.',
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _generating ? null : _generate,
            child: Text(_generating ? 'Generating...' : 'Generate Report'),
          ),
          if (_downloadUrl != null) ...[
            const SizedBox(height: 12),
            SelectableText(_downloadUrl!, style: const TextStyle(fontSize: 12, color: Colors.blue)),
          ],
        ],
      ),
    );
  }
}
