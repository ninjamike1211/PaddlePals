import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class User {
  // final int userId;
  final String username;
  // final String passwordHash;
  // final int valid;
  final int gamesPlayed;
  final int gamesWon;
  final double avgScore;

  User({
    // required this.userId,
    required this.username,
    // required this.passwordHash,
    // required this.valid,
    required this.gamesPlayed,
    required this.gamesWon,
    required this.avgScore
  });

  factory User.fromJson(Map<String, dynamic> json){
    return User(
      username: json['username'],
      gamesPlayed: json['gamesPlayed'],
      gamesWon: json['gamesWon'],
      avgScore: json['averageScore']
    );
  }
}


class MyTextEntryWidget extends StatefulWidget {
  @override
  _MyTextEntryWidgetState createState() => _MyTextEntryWidgetState();
}

class _MyTextEntryWidgetState extends State<MyTextEntryWidget> {
  final TextEditingController _controller = TextEditingController();

  void _printInput() {
    print("Entered: ${_controller.text}");
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          TextField(
            controller: _controller,
            decoration: InputDecoration(
              labelText: 'Enter username',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _printInput,
            child: const Text('Create'),
          )
        ],
      ),
    );
  }
}


class DataService{
  static final DataService _instance = DataService._internal();
  factory DataService() => _instance;
  DataService._internal();

  List<User>? _cachedData;

  Future<List<User>> getRequest() async {
    final url = Uri.parse("http://10.6.27.99:80/pickle/user?user_id=1");
    final response = await http.get(url);

    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200) {
      final body = response.body;

      try {
        final jsonData = json.decode(body);

        if (jsonData is Map<String, dynamic>) {
          // single user object
          return [User.fromJson(jsonData)];
        } else if (jsonData is List) {
          // list of user objects
          return jsonData.map<User>((item) => User.fromJson(item)).toList();
        } else {
          throw FormatException('Unexpected JSON format');
        }
      } catch (e) {
        throw FormatException('Error decoding response: $e');
      }
    } else {
      throw Exception('Failed to fetch data: ${response.statusCode}');
    }
  }

}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(

        colorScheme: ColorScheme.fromSeed(seedColor: Colors.tealAccent),
      ),
      home: MyHomePage(),
    );
  }
}

// class MyAppState extends ChangeNotifier {
//   var current = WordPair.random();
//
//   void getNext() {
//     current = WordPair.random();
//     notifyListeners();
//   }
//
//   var favorites = <WordPair>[];
//
//   void toggleFavorite() {
//     if (favorites.contains(current)) {
//       favorites.remove(current);
//     } else {
//       favorites.add(current);
//     }
//     notifyListeners();
//   }
// }


class MyHomePage extends StatefulWidget {
  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {

  var selectedIndex = 0;


  @override
  Widget build(BuildContext context) {
    Widget page;
    switch (selectedIndex) {
      case 0:
        page = GamePage();
        break;
      case 1:
        page = SocialPage();
        break;
      case 2:
        page = HistoryPage();
        break;
      case 3:
        page = newUserPage();
        break;
      default:
        throw UnimplementedError('no widget for $selectedIndex');
    }

    return LayoutBuilder(
        builder: (context, constraints) {
          return Scaffold(
            body: Row(
              children: [
                SafeArea(
                  child: NavigationRail(
                    extended: constraints.maxWidth >= 600,
                    destinations: [
                      NavigationRailDestination(
                        icon: Icon(Icons.sports_tennis),
                        label: Text('Games'),
                      ),
                      NavigationRailDestination(
                        icon: Icon(Icons.groups),
                        label: Text('My Pals'),
                      ),
                      NavigationRailDestination(
                        icon: Icon(Icons.history),
                        label: Text('History'),
                      ),
                      NavigationRailDestination(
                          icon: Icon(Icons.add),
                          label: Text('Add User'))
                    ],
                    selectedIndex: selectedIndex,
                    onDestinationSelected: (value) {
                      setState(() {
                        selectedIndex = value;
                      });
                    },
                  ),
                ),
                Expanded(
                  child: Container(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    child: page,
                  ),
                ),
              ],
            ),
          );
        }
    );
  }
}

class GamePage extends StatelessWidget{
  const GamePage({super.key});

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('Current Game'),
      ),
      body: const Center(
        child: Text('Placeholder'),
      ),
    );
  }
}

class SocialPage extends StatelessWidget{
  const SocialPage({super.key});

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Pals'),
      ),
      body: Center(
        child: Container( //PUT LIST OF FRIENDS
          width: 100,
          height: 100,
          color: Colors.blue,
          child: Text('Hello'),
        ),
      ),
    );
  }
}

class HistoryPage extends StatelessWidget{
  const HistoryPage({super.key});

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('History'),
      ),
      body: Center(
        child: FutureBuilder<List<User>>(
            future: DataService().getRequest(),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const CircularProgressIndicator();
              } else if (snapshot.hasError) {
                //formatting error here
                return Text('Error: ${snapshot.error}');
              } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                return const Text('No user data available');
              }

              final user = snapshot.data![0]; // get the first user

              return Text('Username: ${user.username}');
            },
        ), //FutureBuilder
      ), //Center
    );
  }
}

class newUserPage extends StatelessWidget{
  const newUserPage({super.key});

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add User'),
      ),
      body: Center(
        child: Column(
          children: [
            MyTextEntryWidget(),
          ],
        ),
      ),
    );
  }
}

