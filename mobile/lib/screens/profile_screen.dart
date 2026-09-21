import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, required this.onLogout});
  final VoidCallback onLogout;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = context.read<ApiService>().me();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snap.hasError) return Center(child: Text('Error: ${snap.error}'));
          final user = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              CircleAvatar(radius: 32, backgroundColor: const Color(0xFF0B2545), child: Text(user['full_name'][0], style: const TextStyle(color: Colors.white, fontSize: 26))),
              const SizedBox(height: 12),
              Text(user['full_name'], style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
              Text(user['officer_id'], textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
              Text(user['role'], textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
              const SizedBox(height: 24),
              const ListTile(leading: Icon(Icons.security_outlined), title: Text('Security')),
              const ListTile(leading: Icon(Icons.notifications_outlined), title: Text('Notifications')),
              ListTile(
                leading: const Icon(Icons.info_outline),
                title: const Text('About PARAKH'),
                onTap: () => showDialog(
                  context: context,
                  builder: (_) => AlertDialog(
                    title: const Text('About PARAKH'),
                    content: const Text(
                      'PARAKH is an inspection-assistance and preliminary compliance-screening system for '
                      'Legal Metrology (Packaged Commodities) Rules, 2011. It identifies potential '
                      'non-compliance and evidence for an authorized officer to verify - it does not '
                      'make a final legal judgment.\n\n'
                      'App Version: 0.1.0 (prototype)\n'
                      'OCR Engine: Tesseract OCR\n'
                      'Rule Engine: configurable',
                    ),
                    actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
                  ),
                ),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.logout, color: Colors.red),
                title: const Text('Logout', style: TextStyle(color: Colors.red)),
                onTap: widget.onLogout,
              ),
            ],
          );
        },
      ),
    );
  }
}
