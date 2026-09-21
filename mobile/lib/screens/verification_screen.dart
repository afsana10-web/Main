import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../widgets/status_badge.dart';

/// Officer verification: CONFIRM / REJECT / MODIFY. The automated finding
/// is displayed but never overwritten - the officer's decision is stored as
/// a separate record (see VerificationRecord on the backend).
class VerificationScreen extends StatefulWidget {
  const VerificationScreen({
    super.key,
    required this.finding,
    required this.check,
    required this.onVerified,
  });

  final Map<String, dynamic> finding;
  final Map<String, dynamic> check;
  final void Function(Map<String, dynamic> updatedFinding) onVerified;

  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  final _correctedValueCtrl = TextEditingController();
  final _remarksCtrl = TextEditingController();
  bool _showModifyForm = false;
  bool _submitting = false;

  Map<String, dynamic>? get _existingVerification => widget.finding['verification'] as Map<String, dynamic>?;

  Future<void> _submit(String decision, {String? correctedValue}) async {
    setState(() => _submitting = true);
    try {
      final api = context.read<ApiService>();
      final updated = await api.verifyFinding(widget.finding['id'], {
        'decision': decision,
        if (correctedValue != null) 'corrected_value': correctedValue,
        'remarks': _remarksCtrl.text.trim(),
      });
      widget.onVerified(updated);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Finding marked ${decision.toLowerCase()}.')));
        Navigator.pop(context, updated);
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Verification failed: $e')));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final alreadyVerified = _existingVerification != null;

    return Scaffold(
      appBar: AppBar(title: const Text('Officer Verification')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.finding['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(height: 6),
                    StatusBadge(status: widget.check['status'] ?? ''),
                    const SizedBox(height: 10),
                    Text('Expected: ${widget.finding['expected'] ?? '-'}'),
                    Text('Detected: ${widget.finding['detected'] ?? '-'}'),
                    const SizedBox(height: 6),
                    Text(widget.check['reason'] ?? '', style: const TextStyle(color: Colors.black87)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            if (alreadyVerified) ...[
              Card(
                color: Colors.grey.shade100,
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Officer Decision: ${_existingVerification!['decision']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                      if (_existingVerification!['corrected_value'] != null)
                        Text('Corrected Value: ${_existingVerification!['corrected_value']}'),
                      if (_existingVerification!['remarks'] != null)
                        Text('Remarks: ${_existingVerification!['remarks']}'),
                      Text('Verified: ${_existingVerification!['verification_date']}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                    ],
                  ),
                ),
              ),
            ] else ...[
              const Text('Automated result — requires your verification.', style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey)),
              const SizedBox(height: 16),
              TextField(
                controller: _remarksCtrl,
                decoration: const InputDecoration(labelText: 'Remarks (optional)'),
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                      onPressed: _submitting ? null : () => _submit('CONFIRMED'),
                      child: const Text('CONFIRM'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                      onPressed: _submitting ? null : () => _submit('REJECTED'),
                      child: const Text('REJECT'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              OutlinedButton(
                onPressed: () => setState(() => _showModifyForm = !_showModifyForm),
                child: const Text('MODIFY FINDING'),
              ),
              if (_showModifyForm) ...[
                const SizedBox(height: 12),
                TextField(
                  controller: _correctedValueCtrl,
                  decoration: const InputDecoration(labelText: 'Corrected Value'),
                ),
                const SizedBox(height: 10),
                ElevatedButton(
                  onPressed: _submitting
                      ? null
                      : () {
                          if (_correctedValueCtrl.text.trim().isEmpty) {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Corrected value is required.')));
                            return;
                          }
                          _submit('MODIFIED', correctedValue: _correctedValueCtrl.text.trim());
                        },
                  child: const Text('Submit Correction'),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}
