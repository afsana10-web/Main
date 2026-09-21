import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import 'processing_screen.dart';

class NewInspectionScreen extends StatefulWidget {
  const NewInspectionScreen({super.key, required this.onDone});
  final VoidCallback onDone;

  @override
  State<NewInspectionScreen> createState() => _NewInspectionScreenState();
}

class _NewInspectionScreenState extends State<NewInspectionScreen> {
  final _productCtrl = TextEditingController();
  final _brandCtrl = TextEditingController();
  final _categoryCtrl = TextEditingController();
  final _locationCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  final _picker = ImagePicker();

  final List<_StagedPhoto> _photos = [];
  static const _categories = ['FRONT', 'BACK', 'SIDE', 'TOP', 'BOTTOM', 'OTHER'];

  Future<void> _addPhoto(ImageSource source) async {
    final file = await _picker.pickImage(source: source, imageQuality: 92);
    if (file == null) return;
    setState(() => _photos.add(_StagedPhoto(path: file.path, category: 'FRONT')));
  }

  void _startAnalysis() {
    if (_productCtrl.text.trim().isEmpty ||
        _brandCtrl.text.trim().isEmpty ||
        _categoryCtrl.text.trim().isEmpty ||
        _locationCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please fill in all required product details.')));
      return;
    }
    if (_photos.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please add at least one package image.')));
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ProcessingScreen(
          inspectionPayload: {
            'product_name': _productCtrl.text.trim(),
            'brand': _brandCtrl.text.trim(),
            'category': _categoryCtrl.text.trim(),
            'location': _locationCtrl.text.trim(),
            'notes': _notesCtrl.text.trim(),
          },
          images: _photos.map((p) => StagedImage(filePath: p.path, category: p.category)).toList(),
          onFinished: widget.onDone,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New Inspection')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Product Details', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          TextField(controller: _productCtrl, decoration: const InputDecoration(labelText: 'Product Name')),
          const SizedBox(height: 10),
          TextField(controller: _brandCtrl, decoration: const InputDecoration(labelText: 'Brand')),
          const SizedBox(height: 10),
          TextField(controller: _categoryCtrl, decoration: const InputDecoration(labelText: 'Product Category')),
          const SizedBox(height: 10),
          TextField(controller: _locationCtrl, decoration: const InputDecoration(labelText: 'Inspection Location')),
          const SizedBox(height: 10),
          TextField(controller: _notesCtrl, decoration: const InputDecoration(labelText: 'Notes'), maxLines: 3),
          const SizedBox(height: 24),
          const Text('Package Images', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: const Text('Camera'),
                  onPressed: () => _addPhoto(ImageSource.camera),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Gallery'),
                  onPressed: () => _addPhoto(ImageSource.gallery),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_photos.isEmpty)
            const Padding(padding: EdgeInsets.symmetric(vertical: 16), child: Text('No images added yet.', style: TextStyle(color: Colors.grey)))
          else
            ..._photos.asMap().entries.map((entry) {
              final idx = entry.key;
              final photo = entry.value;
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: Image.file(File(photo.path), width: 48, height: 48, fit: BoxFit.cover),
                  ),
                  title: DropdownButton<String>(
                    value: photo.category,
                    isExpanded: true,
                    items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                    onChanged: (v) => setState(() => photo.category = v!),
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () => setState(() => _photos.removeAt(idx)),
                  ),
                ),
              );
            }),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _startAnalysis,
            child: const Padding(padding: EdgeInsets.symmetric(vertical: 4), child: Text('START ANALYSIS')),
          ),
        ],
      ),
    );
  }
}

class _StagedPhoto {
  _StagedPhoto({required this.path, required this.category});
  final String path;
  String category;
}
