import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/status_badge.dart';
import 'inspection_detail_screen.dart';

class InspectionHistoryScreen extends StatefulWidget {
  const InspectionHistoryScreen({super.key});

  @override
  State<InspectionHistoryScreen> createState() => _InspectionHistoryScreenState();
}

class _InspectionHistoryScreenState extends State<InspectionHistoryScreen> {
  final _searchCtrl = TextEditingController();
  String? _statusFilter;
  List<dynamic> _items = [];
  bool _loading = true;
  String? _error;

  static const _statuses = [
    'COMPLIANT', 'POTENTIAL_NON_COMPLIANCE', 'NEEDS_OFFICER_VERIFICATION', 'PENDING', 'PROCESSING', 'FAILED',
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final api = context.read<ApiService>();
      final query = <String, String>{};
      if (_searchCtrl.text.trim().isNotEmpty) query['search'] = _searchCtrl.text.trim();
      if (_statusFilter != null) query['status'] = _statusFilter!;
      final items = await api.listInspections(query: query);
      setState(() { _items = items; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Inspections')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                TextField(
                  controller: _searchCtrl,
                  decoration: InputDecoration(
                    hintText: 'Search product, brand, or ID',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: IconButton(icon: const Icon(Icons.arrow_forward), onPressed: _load),
                  ),
                  onSubmitted: (_) => _load(),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 36,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: [
                      _filterChip('All', _statusFilter == null, () { setState(() => _statusFilter = null); _load(); }),
                      ..._statuses.map((s) => Padding(
                            padding: const EdgeInsets.only(left: 6),
                            child: _filterChip(s.replaceAll('_', ' '), _statusFilter == s, () { setState(() => _statusFilter = s); _load(); }),
                          )),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(child: Text('Error: $_error'))
                    : _items.isEmpty
                        ? const Center(child: Text('No inspections match these filters.', style: TextStyle(color: Colors.grey)))
                        : RefreshIndicator(
                            onRefresh: _load,
                            child: ListView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 12),
                              itemCount: _items.length,
                              itemBuilder: (context, i) {
                                final item = _items[i];
                                return Card(
                                  margin: const EdgeInsets.only(bottom: 8),
                                  child: ListTile(
                                    title: Text(item['product_name'] ?? ''),
                                    subtitle: Text('${item['inspection_code']} · ${item['category']}'),
                                    trailing: StatusBadge(status: item['status'] ?? ''),
                                    onTap: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(builder: (_) => InspectionDetailScreen(inspectionId: item['id'])),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String label, bool selected, VoidCallback onTap) {
    return ChoiceChip(label: Text(label, style: const TextStyle(fontSize: 11)), selected: selected, onSelected: (_) => onTap());
  }
}
