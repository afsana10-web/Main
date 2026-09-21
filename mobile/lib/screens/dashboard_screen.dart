import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/status_badge.dart';
import 'new_inspection_screen.dart';
import 'inspection_detail_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<Map<String, dynamic>> _statsFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _statsFuture = context.read<ApiService>().dashboardStats();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PARAKH')),
      body: RefreshIndicator(
        onRefresh: () async { setState(_load); await _statsFuture; },
        child: FutureBuilder<Map<String, dynamic>>(
          future: _statsFuture,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text('Failed to load dashboard: ${snap.error}'))]);
            }
            final stats = snap.data!;
            final recent = (stats['recent_inspections'] as List).cast<Map<String, dynamic>>();
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  childAspectRatio: 1.6,
                  children: [
                    _StatCard(label: 'Total Inspections', value: '${stats['total_inspections']}', color: ParakhColors.navy900),
                    _StatCard(label: 'Compliant', value: '${stats['compliant']}', color: ParakhColors.green),
                    _StatCard(label: 'Potential Issues', value: '${stats['potential_issues']}', color: ParakhColors.amber),
                    _StatCard(label: 'Pending Verification', value: '${stats['pending_verification']}', color: ParakhColors.blue),
                  ],
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Recent Inspections', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    TextButton.icon(
                      icon: const Icon(Icons.add),
                      label: const Text('New Inspection'),
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => NewInspectionScreen(onDone: () => Navigator.pop(context)))),
                    ),
                  ],
                ),
                if (recent.isEmpty)
                  const Padding(padding: EdgeInsets.all(24), child: Text('No inspections yet.', style: TextStyle(color: Colors.grey)))
                else
                  ...recent.map((i) => Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          title: Text(i['product_name'] ?? ''),
                          subtitle: Text('${i['inspection_code']} · ${i['category']}'),
                          trailing: StatusBadge(status: i['status'] ?? ''),
                          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => InspectionDetailScreen(inspectionId: i['id']))),
                        ),
                      )),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value, required this.color});
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Container(
        decoration: BoxDecoration(border: Border(left: BorderSide(color: color, width: 3))),
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
