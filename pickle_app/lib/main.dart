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
}

class DataService{
  static final DataService _instance = DataService._internal();
  factory DataService() => _instance;
  DataService._internal();

  List<User>? _cachedData;

  Future<List<User>> getRequest() async {
    if (_cachedData != null) return _cachedData!;

    String url = "http://localhost:8080/pickle/user?user_id=3";

    final response = await http.get(Uri.parse(url));

    var responseData = json.decode(response.body);

    List<User> usersList = [];
    for(var singleUser in responseData){
      User user = User(
        // userId: singleUser["user_id"], //check what the names are in the database
          username: singleUser["username"],
          // passwordHash: singleUser["passwordHash"],
          // valid: singleUser["valid"],
          gamesPlayed: singleUser["gamesPlayed"],
          gamesWon: singleUser["gamesWon"],
          avgScore: singleUser["averageScore"]
      );
      usersList.add(user);
    }
    _cachedData = usersList;
    return usersList;
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

