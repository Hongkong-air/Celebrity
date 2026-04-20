import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../services/api_service.dart';
import '../../services/auth_service.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('个人中心')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 用户头像
          const Center(
            child: CircleAvatar(
              radius: 48,
              backgroundColor: Color(0xFF6B5CE7),
              child: Icon(Icons.person, size: 48, color: Colors.white),
            ),
          ),
          const SizedBox(height: 16),
          Center(
            child: FutureBuilder<String?>(
              future: _getUsername(),
              builder: (context, snapshot) {
                return Text(
                  snapshot.data ?? '加载中...',
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                );
              },
            ),
          ),
          const SizedBox(height: 32),

          // 设置项
          _SettingsTile(
            icon: Icons.history,
            title: '对话历史',
            subtitle: '查看与先贤的对话记录',
            onTap: () {},
          ),
          _SettingsTile(
            icon: Icons.volume_up,
            title: '语音设置',
            subtitle: '调整 TTS 语速和音色',
            onTap: () {},
          ),
          _SettingsTile(
            icon: Icons.palette,
            title: '主题设置',
            subtitle: '切换深色/浅色模式',
            onTap: () {},
          ),
          _SettingsTile(
            icon: Icons.info_outline,
            title: '关于',
            subtitle: '人类群星闪耀时 v1.0.0',
            onTap: () {},
          ),
          const Divider(height: 32),
          _SettingsTile(
            icon: Icons.logout,
            title: '退出登录',
            subtitle: '',
            iconColor: Colors.red,
            titleColor: Colors.red,
            onTap: () async {
              await ApiService.clearToken();
              if (context.mounted) context.read<AuthProvider>().logout();
            },
          ),
        ],
      ),
    );
  }

  Future<String?> _getUsername() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');
      if (token == null) return null;
      return '用户';
    } catch (_) {
      return null;
    }
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final Color? iconColor;
  final Color? titleColor;

  const _SettingsTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.iconColor,
    this.titleColor,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: iconColor),
      title: Text(title, style: TextStyle(color: titleColor)),
      subtitle: subtitle.isNotEmpty ? Text(subtitle) : null,
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }
}
