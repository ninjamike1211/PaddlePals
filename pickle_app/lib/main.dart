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

  Map<String, dynamic> toJson() => {
    'username': username,
    'gamesPlayed': gamesPlayed,
    'gamesWon': gamesWon,
    'averageScore': avgScore
  };
}

List<User> usersList = [];

/*
CLASS FOR ALL API REQUESTS
 */
class APIRequests {
  final String url = "http://10.5.105.211:80";

  //GET REQUEST
  Future<List<User>> getRequest(String endpoint) async {
    final response = await http.get(Uri.parse('$url$endpoint'));

    //success
    if(response.statusCode == 200){
      final body = response.body;

      //format into List<User> and check JSON decoding
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
    }
    else{
      throw Exception('GET request FAILED: ${response.statusCode}');
    }
  }

  Future<dynamic> postNewUserRequest(String un, String pw) async {
    print(un);
    print(pw);
    Map<String, String> newUser = {
      'username': un.trim(),
      'password': pw.trim(),
    };

    print(newUser);
    String endpoint = "/pickle/user";


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(newUser),
    );

    print("Sent JSON: ${jsonEncode(newUser)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }
}

final api = APIRequests();

class MyTextEntryWidget extends StatefulWidget {
  @override
  _MyTextEntryWidgetState createState() => _MyTextEntryWidgetState();
}

class _MyTextEntryWidgetState extends State<MyTextEntryWidget> {
  final TextEditingController _controller1 = TextEditingController();
  final TextEditingController _controller2 = TextEditingController();

  _createNewUser(String userName, String password) {
    // final newUser = User(
    //   username: newName,
    //   gamesPlayed: 0,
    //   gamesWon: 0,
    //   avgScore: 0
    // );

    // usersList.add(newUser);

    api.postNewUserRequest(userName, password);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          TextField(
            controller: _controller1,
            decoration: InputDecoration(
              labelText: 'Enter username',
              border: OutlineInputBorder(),
            ),
          ),
          TextField(
            controller: _controller2,
            decoration: InputDecoration(
              labelText: 'Enter password',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: (){
              _createNewUser(_controller1.text, _controller2.text);
            },
            child: const Text('Create'),
          )
        ],
      ),
    );
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
            future: api.getRequest("/pickle/user?user_id=1"),
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

class newUserPage extends StatefulWidget{
  const newUserPage({super.key});

  @override
  State<newUserPage> createState() => _newUserPageState();
}

class _newUserPageState extends State<newUserPage> {

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

