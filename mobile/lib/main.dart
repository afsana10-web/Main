import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/home_shell.dart';

void main() {
  runApp(const ParakhApp());
}

class ParakhApp extends StatelessWidget {
  const ParakhApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Provider<ApiService>(
      create: (_) => ApiService(),
      child: MaterialApp(
        title: 'PARAKH',
        debugShowCheckedModeBanner: false,
        theme: buildParakhTheme(),
        home: const _AuthGate(),
      ),
    );
  }
}

/// Decides whether to show the login screen or the authenticated app shell,
/// based on whether a JWT is already stored securely on-device.
class _AuthGate extends StatefulWidget {
  const _AuthGate();

  @override
  State<_AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<_AuthGate> {
  bool _checking = true;
  bool _authenticated = false;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final api = context.read<ApiService>();
    final token = await api.getToken();
    if (token == null) {
      setState(() { _checking = false; _authenticated = false; });
      return;
    }
    try {
      await api.me();
      setState(() { _checking = false; _authenticated = true; });
    } catch (_) {
      await api.clearToken();
      setState(() { _checking = false; _authenticated = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _authenticated
        ? const HomeShell()
        : LoginScreen(onLoggedIn: () => setState(() => _authenticated = true));
  }
}
