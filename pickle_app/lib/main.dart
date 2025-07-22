import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'dart:async';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider/path_provider.dart';


void main() async{
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();
  await Hive.openBox('cacheBox'); // Open a box for caching

  runApp(ChangeNotifierProvider(
    create: (context) => User(username: "", gamesPlayed: 0, gamesWon: 0, avgScore: 0),
    child: MyApp(),));
}


/*
CLASS FOR ALL API REQUESTS
 */
class APIRequests {
  final String url = "http://10.0.0.188:80";

  //GET REQUEST
  Future<Map<String, dynamic>> getUserRequest(int id_num) async {
    //"/pickle/user/get?user_id=1"
    Map<String, int> u_id = {
      'user_id': id_num,
    };

    print(u_id);
    String endpoint = "/pickle/user/get";
    print("$endpoint");
    //NOTE Authorization header for authorization api (look up standard authorization header, Bearer)

    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(u_id)).timeout(const Duration(seconds:10));
    print('Status ${response.statusCode}');

    print("Sent JSON: ${jsonEncode(u_id)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){

      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> postNewUserRequest(String un, String pw) async {
    print(un);
    print(pw);
    Map<String, String> newUser = {
      'username': un.trim(),
      'password': pw.trim(),
    };

    print(newUser);
    String endpoint = "/pickle/user/create";
    print("$endpoint");


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
  Future<Map<String, dynamic>> getUserID(String un) async {
    print(un);
    Map<String, String> userToSearch = {
      'username': un.trim(),
    };

    print(userToSearch);
    String endpoint = "/pickle/user/id";
    print("$endpoint");

    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(userToSearch),
    );

    print("Sent JSON: ${jsonEncode(userToSearch)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getFriends(String un) async {
    print(un);

    Map<String, dynamic> user_id = await getUserID(un);

    final int id_num = user_id[un];

    print("username: $un user_id: $id_num");

    Map<String, dynamic> params = {
      'user_id': id_num,
      // 'include_username': true
    };

    print(params);
    String endpoint = "/pickle/user/friends";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      // print(json.decode(response.body));
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> addFriend(String un, String friendUN) async {
    print(un);

    Map<String, dynamic> user_id = await getUserID(un);

    final int id_num = user_id[un];

    print("username: $un user_id: $id_num");

    Map<String, dynamic> params = {
      'user_id': id_num,
      'friend_username': friendUN
    };

    print(params);
    String endpoint = "/pickle/user/addFriend";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      // print(json.decode(response.body));
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<bool> authorizeLogin(String un, String pw) async {
    print("Username: $un");
    print("Password: $pw");

    Map<String, dynamic> params = {
      'username': un.trim(),
      'password': pw.trim()
    };

    print("Params: $params");
    String endpoint = "/pickle/user/auth";
    print("Endpoint: $endpoint");

    final bodyBytes = utf8.encode(json.encode(params));
    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': bodyBytes.length.toString(),
      },
      body: bodyBytes,
    );

    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201) {
      if (response.body.isNotEmpty) {
        final Map<String, dynamic> responseData = json.decode(response.body);
        return responseData['success'] == true;
      }
    }
    return false;
  }

  Future<Map<String, dynamic>> registerGame(int timestamp, int gameTypeNum, String winnerName, String loserName, int winnerPoints, int loserPoints) async{
    Map<String, dynamic> winner_id = await getUserID(winnerName);
    final int winner_id_num = winner_id[winnerName];

    Map<String, dynamic> loser_id = await getUserID(loserName);
    final int loser_id_num = loser_id[loserName];

    Map<String, dynamic> params = {
      'timestamp': timestamp,
      'game_type': gameTypeNum,
      'winner_id': winner_id_num,
      'loser_id': loser_id_num,
      'winner_points': winnerPoints,
      'loser_points': loserPoints
    };

    print(params);
    String endpoint = "/pickle/game/register";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      // print(json.decode(response.body));
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getUsersGames(String un) async {
    Map<String, dynamic> user_id = await getUserID(un);
    final int user_id_num = user_id[un];

    Map<String, dynamic> params = {
      'user_id': user_id_num
    };

    print(params);
    String endpoint = "/pickle/user/games";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      // print(json.decode(response.body));
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getGameInfo(int gameID) async {
    Map<String, dynamic> params = {
      'game_id': gameID
    };

    print(params);
    String endpoint = "/pickle/game/get";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      // print(json.decode(response.body));
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getGameStats(int gameID, String un) async {
    Map<String, dynamic> user_id = await getUserID(un);
    final int user_id_num = user_id[un];

    Map<String, dynamic> params = {
      'game_id': gameID,
      'user_id' : user_id_num
    };

    print(params);
    String endpoint = "/pickle/game/stats";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      // print(json.decode(response.body));
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getUsername(int userId) async {

    Map<String, dynamic> params = {
      'user_id': userId,
      'values' : 'username'
    };

    print(params);
    String endpoint = "/pickle/user/get";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      // print(json.decode(response.body));
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }


}

final api = APIRequests();

class User extends ChangeNotifier {
  // final int userId;
  String username;
  // final String passwordHash;
  // final int valid;
  int gamesPlayed;
  int gamesWon;
  double avgScore;
  List<Map<String,dynamic>> pals;
  String opponent;

  User({
    required this.username,
    required this.gamesPlayed,
    required this.gamesWon,
    required this.avgScore,
    this.pals = const [],  // default to empty list
    this.opponent = ""
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

  Future<void> updateUserfromDatabase(String newUserName) async{

    print("in updateUserfromDatabase");
    Map<String, dynamic> user_id = await api.getUserID(newUserName);

    final int id_num = user_id[newUserName];

    Map<String, dynamic> newUserMap = await api.getUserRequest(id_num);
    Map<String, dynamic> userMap = newUserMap['2'];

    Map<String, dynamic> friendMap = await api.getFriends(newUserName);

    List<Map<String, dynamic>> friendList = [];

    friendMap.forEach((id, data) {
      friendList.add(data);
    });

    username = userMap['username'];
    gamesPlayed = userMap['gamesPlayed'];
    gamesWon = userMap['gamesWon'];
    avgScore = userMap['averageScore'];
    pals = friendList;

    notifyListeners();
  }

  void setOpponent(String opponentName){
    opponent = opponentName;
    notifyListeners();
  }

}

class BleFunctionality{

  final FlutterReactiveBle flutterReactiveBle = FlutterReactiveBle();
  final List<DiscoveredDevice> devices = [];
  late StreamSubscription<DiscoveredDevice> scanSubscription;
  late StreamSubscription<ConnectionStateUpdate> connection;
  DiscoveredDevice? connectedDevice;

  BleFunctionality();

  Future<bool> requestPermissions() async {
    final status = await [
      Permission.location,
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
    ].request();

    return status.values.every((s) => s.isGranted);
  }

  Future<void> startScan({required void Function(DiscoveredDevice) onDeviceDiscovered}) async {
    bool granted = await requestPermissions();
    if(granted) {
      flutterReactiveBle.statusStream.listen((status) {
        if (status == BleStatus.ready) {
          print("Ready for BLE discovery");
          scanSubscription = flutterReactiveBle
              .scanForDevices(withServices: <Uuid>[])
              .listen((device) {
            // Add to list if not already present
            final known = devices.any((d) => d.id == device.id);
            if (!known) {
              devices.add(device);
              onDeviceDiscovered(device);
            }
          }, onError: (error) {
            print('Scan error: $error');
          });
        }
        else {
          print("BLE status: $status ");
        }
      });
    }
    else{
      print("Permissions not granted");
    }
  }

  Future<void> connectDevice(DiscoveredDevice selectedDevice, void Function(bool) connectionStatus) async {
    connection = flutterReactiveBle.connectToDevice(id: selectedDevice.id).listen((connectionState) {
      print("Connection State for device ${selectedDevice
          .name} : ${connectionState.connectionState}");
      if (connectionState.connectionState == DeviceConnectionState.connected) {
        connectionStatus(true);
        connectedDevice = selectedDevice;
        print("connected");
      }
      else if (connectionState.connectionState ==
          DeviceConnectionState.disconnected) {
        connectionStatus(false);
        connectedDevice = null;
        print("disconnected");
      }
    }, onError: (Object error){
      print("Connecting to device resulted in error $error");
    });
  }

  void readLiveFromDevice({
    required DiscoveredDevice connectedDevice,
    required Uuid serviceUuid,
    required Uuid characteristicUuid,
    required Function(String) onData,
    required Function(String) onError,
  }){


    final characteristic = QualifiedCharacteristic(
        characteristicId: characteristicUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice.id);

    final response = flutterReactiveBle.subscribeToCharacteristic(characteristic).listen(
          (data) {
        // Convert List<int> to readable value
        final stringValue = String.fromCharCodes(data);
        print("read $stringValue");
        onData(stringValue);
      },
      onError: (error) {
        onError("Error reading string data $error");
      },
    );
  }
}

final myBLE = BleFunctionality();

class Game {
  bool inProgress = false;
  bool isFinished = false;
  int myScore = 0;
  int opponentScore = 0;
  bool playingWithFriend = false;
  String opponentName = "Opponent";
  String winner = "";
  String gameType = "Standard";
  int startTime = 0;

  void incMyScore(){
    myScore += 1;
  }

  void incOppScore(){
    opponentScore += 1;
  }

  bool checkForWinner(){
    if (myScore >= 11 && opponentScore <= myScore - 2){
      inProgress = false;
      isFinished = true;

      return true;
    }
    else if(opponentScore >= 11 && myScore <= opponentScore - 2){
      inProgress = false;
      isFinished = true;
      return true;
    }
    else{
      return false;
    }
  }

  String getWinner(){
    if (checkForWinner()){
      if (myScore > opponentScore) {
        winner = "me";
        return winner;
      }
      else{
        winner = "opponent";
        return winner;
      }
    }
    else{
      return "no winner";
    }
  }

  void startGame(){
    inProgress = true;
    startTime = DateTime.now().millisecondsSinceEpoch ~/ 1000; //in seconds
  }

  void resetGame(){
    inProgress = false;
    isFinished = false;
    myScore = 0;
    opponentScore = 0;
    playingWithFriend = false;
    opponentName = "Opponent";
    winner = "";
  }

  int gameTypeToInt(){
    if (gameType == "Standard"){
      return 0;
    }
    else{
      print("invalid game type");
      return -1;
    }
  }

}

class ConnectivityCheck {
  static final ConnectivityCheck _instance = ConnectivityCheck._internal();
  factory ConnectivityCheck() => _instance;
  ConnectivityCheck._internal(){
    _init();
  }

  final _connectivity = Connectivity();
  final ValueNotifier<bool> isOnline = ValueNotifier(true);

  void _init() async{
    await _checkInitStatus();

    _connectivity.onConnectivityChanged.listen((result){
      final online = !result.contains(ConnectivityResult.none);
      isOnline.value = online;
    });

  }

  Future<void> _checkInitStatus() async {
    final result = await _connectivity.checkConnectivity();
    final online = !result.contains(ConnectivityResult.none);
    isOnline.value = online;
    print('Initial connectivity: $result');

    // Delay the print to ensure ValueNotifier has processed the change
    Future.microtask(() {
      print('isOnline after update: ${isOnline.value}');
    });
  }

  //listen for a restored connection, then send previously cached data to database
  void connectionRestoreListener(VoidCallback sendCachedData){
    //check previous connection state
    bool wasOffline = !isOnline.value;

    isOnline.addListener(() {
      //connection was restored
      if (isOnline.value && wasOffline){
        sendCachedData();
      }
      //reset value
      wasOffline = !isOnline.value;
    });

  }
}


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

  _login(String userName, String password) async {
    bool validLogin = await api.authorizeLogin(userName, password);

    if(validLogin){
      Provider.of<User>(context, listen: false).updateUserfromDatabase(userName);
      Navigator.pushReplacementNamed(context, '/home');
    }
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
          SizedBox(
            height: 16,
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
              _login(_controller1.text, _controller2.text);
            },
            child: const Text('Login'),
          )
        ],
      ),
    );
  }
}


//User will probably be an app state
class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  // This widget is the root of your application.
  //User currentUser = User(username: "", gamesPlayed: 0, gamesWon: 0, avgScore: 0);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PicklePals',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.tealAccent),
        scaffoldBackgroundColor: Colors.white,
      ),
      initialRoute: '/', // Start at Login
      routes: {
        '/': (context) => LoginPage(),
        '/home': (context) => MyHomePage(),
      },
    );
  }
}

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
        page = ProfilePage();
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
                          icon: Icon(Icons.person),
                          label: Text('ProfileS')
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
                    color: Colors.white,
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

class GamePage extends StatefulWidget{
  const GamePage({super.key});

  @override
  State<GamePage> createState() => _GamePageState();
}

class _GamePageState extends State<GamePage> {
  var game = Game();
  bool isLoading = true;
  final serviceUuid = Uuid.parse("91bad492-b950-4226-aa2b-4ede9fa42f59");
  final characteristicUuid = Uuid.parse("ca73b3ba-39f6-4ab3-91ae-186dc9577d99");
  final internetConnection = ConnectivityCheck();


  void loadOpponent(){
    if(context.read<User>().opponent != ""){
      game.opponentName = context.read<User>().opponent;
    }
    else{
      game.opponentName = "Opponent";
    }

    setState(() {
      isLoading = false;
    });
  }


  String getTitle(){
    String title = "";
    if (game.inProgress){
      title = "Current Game";
    }
    else if (game.isFinished){
      title = "Finished Game";
    }
    else{
      title = "Start a Game";
    }

    return title;
  }

  void startStandardGame(){
    setState(() {
      game.startGame();
    });
    print("game started");
  }

  String showWinnerContent(String winnerName) {
    if(internetConnection.isOnline.value == true){
      return "$winnerName is the winner!";
    }
    else{
      return "$winnerName is the winner!\nData will be saved locally until connection is restored";
    }
  }
  void showWinner(String winnerName){
    showDialog(
        context: context,
        builder: (BuildContext context){
          return AlertDialog(
            title: Text("Game Over"),
            content: Text(showWinnerContent(winnerName)),
            actions: [
              TextButton(
                  onPressed: saveAndRestartGame,
                  child: Text("Save and Restart")
              )
            ],
          );
        }
    );
  }

  void incMyScore(){
    setState(() {
      game.incMyScore();
    });
    print("My Score: ${game.myScore}");
    if (game.checkForWinner()){
      print("Finished? ${game.isFinished}");
      final winnerName = context.read<User>().username;
      showWinner(winnerName);
    }
  }

  void incOppScore(){
    setState(() {
      game.incOppScore();
    });
    print("Opp score: ${game.opponentScore}");
    if (game.checkForWinner()){
      print("Finished? ${game.isFinished}");
      final winnerName = game.opponentName;
      showWinner(winnerName);
    }
  }

  Future<void> cacheGame(int startTime, int gameTypeNum, String winnerName, String loserName, int winnerPoints, int loserPoints) async {
    Map<String, dynamic> gameToSave = {
      'timestamp': startTime,
      'game_type': gameTypeNum,
      'winner_name': winnerName, //NEED TO BE CONVERTED TO ID BEFORE SENDING TO DATABASE
      'loser_name': loserName,
      'winner_points': winnerPoints,
      'loser_points': loserPoints
    };

    final cacheBox = await Hive.openBox("gameQueue");
    await cacheBox.add(gameToSave);

  }

  void sendCachedGames() async {
    final cacheBox = await Hive.openBox("gameQueue");
    final cacheBoxKeys = cacheBox.keys.toList();

    for(final key in cacheBoxKeys){
      //TODO check formatting and then process accordingly for api call
      final gameData = cacheBox.get(key);
      print(gameData);
      api.registerGame(gameData['timestamp'], gameData['game_type'], gameData['winner_name'], gameData['loser_name'], gameData['winner_points'], gameData['loser_points']);
    }
  }

  void saveAndRestartGame(){
    int gameTypeNum = game.gameTypeToInt();

    String winnerName = "";
    String loserName = "";

    int winnerPoints = -1;
    int loserPoints = -1;

    //handle no registered opponent
    if (game.opponentName == "Opponent"){
      //eventually change to NULL user
      game.opponentName = "testUser";
    }

    if(game.getWinner() == "me"){
      winnerName = context.read<User>().username;
      loserName = game.opponentName;

      winnerPoints = game.myScore;
      loserPoints = game.opponentScore;
    }
    else{
      winnerName = game.opponentName;
      loserName = context.read<User>().username;

      winnerPoints = game.opponentScore;
      loserPoints = game.myScore;
    }

    if(internetConnection.isOnline.value == true){
      api.registerGame(game.startTime, gameTypeNum, winnerName, loserName, winnerPoints, loserPoints);
      print("Online. Sending game to database");
    }
    else{
      cacheGame(game.startTime, gameTypeNum, winnerName, loserName, winnerPoints, loserPoints);
      print("Offline. Caching game data");
    }


    context.read<User>().setOpponent("");

    setState(() {
      game.resetGame();
    });
  }



  @override
  void initState() {
    super.initState();
    loadOpponent();

    internetConnection.connectionRestoreListener((){
      print("Internet connection restored. Sending cached games");
      sendCachedGames();
    });

    if(myBLE.connectedDevice != null){
      DiscoveredDevice device = myBLE.connectedDevice!;

      myBLE.readLiveFromDevice(
        connectedDevice: device,
        serviceUuid: serviceUuid,
        characteristicUuid: characteristicUuid,
        onData: (data) {
          setState(() {
            game.myScore = int.tryParse(data) ?? 0;
          });
        },
        onError: (error) {
          setState(() {
            game.myScore = -1;
          });
        },
      );
    }

  }

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: Text(
            getTitle()
        ),
      ),
      body:
      Column(
        children: [
          ValueListenableBuilder(
              valueListenable: internetConnection.isOnline,
              builder: (context, online, _){
                print("Game Page Connectivity: $online");
                return online ? Text("") : Text("Offline");
              }
          ),
          Row(
            children: [
              SizedBox(width: 80,),
              Text(
                "Me",
                style: TextStyle(
                    fontSize: 24
                ),
              ),
              SizedBox(width: 70,), //,may need to make spacing variable depending opponentName
              Text(
                game.opponentName,
                style: TextStyle(
                    fontSize: 24
                ),
              ),
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                height: 200,
                width: 125,
                decoration:BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    border: Border.all(
                        color: Colors.black,
                        width: 2
                    )
                ),
                alignment: Alignment.center,
                child: Text(
                  game.myScore.toString(),
                  style: TextStyle(
                      fontSize: 40
                  ),
                ),

              ),
              SizedBox(width: 16),
              Container(
                  height: 200,
                  width: 125,
                  decoration:BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      border: Border.all(
                          color: Colors.black,
                          width: 2
                      )
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    game.opponentScore.toString(),
                    style: TextStyle(
                        fontSize: 40
                    ),
                  )
              ),
            ],
          ),
          Text("Game type: ${game.gameType}"),
          ElevatedButton(
              onPressed: startStandardGame,
              child: Text("Start Game")
          ),
          ElevatedButton(
              onPressed: incMyScore,
              child: Text("Inc my score")
          ),
          ElevatedButton(
              onPressed: incOppScore,
              child: Text("Inc opp score")
          ),
        ],
      ),
    );
  }
}

class SocialPage extends StatefulWidget{
  const SocialPage({super.key});

  @override
  State<SocialPage> createState() => _SocialPageState();
}

class _SocialPageState extends State<SocialPage> {

  final TextEditingController _controller = TextEditingController();
  bool isLoading = true;
  final internetConnection = ConnectivityCheck();

  @override
  void initState() {
    super.initState();
    loadUser();
  }

  Future<void> loadUser() async {
    final username = context.read<User>().username;
    await context.read<User>().updateUserfromDatabase(username);
    setState(() {
      isLoading = false;
    });
  }

  Future<void> showFriends(String username) async{
    try{
      var friends = await api.getFriends(username);
      print("Friends: $friends");
      print(friends.runtimeType);
    } catch(e){
      print("error getting friends: $e");
    }
  }

  Future<void> addFriend(String username, String friendUsername) async{
    try{
      var success = await api.addFriend(username, friendUsername.trim());
      print(success["success"]);
      if(success["success"]){
        await context.read<User>().updateUserfromDatabase(username);
        // friends = get friends
      }
      showFriends(username);
    } catch (e){
      print("error adding friend: $e");
    }

  }

  //TODO
  void deletePal(String palName){
    print("Delete button $palName");
  }

  void startGameWithPal(String palName){
      print("Start game with $palName");
      context.read<User>().setOpponent(palName);
  }

  void showOptions(String palName){
    showDialog(
        context: context,
        builder: (BuildContext context){
          return AlertDialog(
            title: Text("Pal Options"),
            actions: [
              TextButton(
                  onPressed: () {
                    Navigator.of(context).pop(); // close the dialog
                  },
                  child: Text("Cancel")
              ),
              TextButton(
                  onPressed: () {
                    deletePal(palName);
                    Navigator.of(context).pop();
                  },
                  child: Text("Delete")
              ),
              TextButton(
                  onPressed: () {
                    startGameWithPal(palName);
                    Navigator.of(context).pop();
                  },
                  child: Text("Start Game"),
              )
            ],
          );
        }
    );
  }

  @override
  Widget build(BuildContext context){
    final user = context.watch<User>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Pals'),
      ),
      body: Center(
        child:
        Column(
          children: [
            ValueListenableBuilder(
                valueListenable: internetConnection.isOnline,
                builder: (context, online, _){
                  print("Game Page Connectivity: $online");
                  return online ? Text("") : Text("Offline");
                }
            ),
            SizedBox(height: 16),
            SizedBox(
              width: 300,
              child: TextField(
                controller: _controller,
                decoration: InputDecoration(
                  labelText: 'Enter friend\'s username:',
                  border: OutlineInputBorder(),
                ),

              ),
            ),
            SizedBox(height: 10),
            ElevatedButton(
                onPressed: () => addFriend(user.username, _controller.text),
                child: Text("Add Friend")
            ),
            Expanded(
              child: ListView.builder(
                  itemCount: user.pals.length,
                  itemBuilder: (context, index) {
                    final pal = user.pals[index];
                    return ListTile(
                      leading: Icon(Icons.person),
                      title: Text(pal['username']),
                      subtitle: Text("Winning %: ${pal['winRate'].toStringAsFixed(3)} Games Played: ${pal['gamesPlayed']}"),
                      onTap: () => showOptions(pal['username']), //show dialog with start game and delete options
                    );
                }
              ),
            )
          ],
        ),
        ),
    );
  }
}

class HistoryPage extends StatefulWidget{
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  List<String> statsToView = ["Wins", "Losses", "Opponents", "Points Scored", "Swing Speeds", "Hit Locations"];
  String? selectedStat;
  List<int>? gameIds;
  List<int>? winIds;
  List<int>? lossIds;
  final internetConnection = ConnectivityCheck();

  @override
  void initState() {
    super.initState();
    //once ui is built, load api calls and context to get games history
    WidgetsBinding.instance.addPostFrameCallback((_) => loadGamesHistory());
  }

  Future<void> loadGamesHistory() async {
    final currentUsername = context.read<User>().username;
    final data = await api.getUsersGames(currentUsername);

    List<dynamic> gameIdDynamic = data['game_ids'] ?? [];
    print("Raw gameIdDynamic: $gameIdDynamic");
    print("Types: ${gameIdDynamic.map((e) => e.runtimeType).toList()}");
    List<int> gameIdNums = gameIdDynamic.cast<int>();

    if (mounted) {
      setState(() {
        gameIds = gameIdNums;
      });
    }
  }

  Future<List<Map<String, dynamic>>> getWins(String username) async {
    List<Map<String, dynamic>> winsList = [];
    List<int> tempWinIds = [];

    if (gameIds != null){
      List<int> tempIds = gameIds ?? [];
      for (var game in tempIds){
          Map<String, dynamic> gameMap = await api.getGameInfo(game);
          print(gameMap);
          String gameIdString = game.toString();
          var winnerId = gameMap[gameIdString]?["winner_id"];
          Map<String, dynamic> winnerMap = await api.getUsername(winnerId);
          String winnerIdString =  winnerId.toString();
          String winnerName = winnerMap[winnerIdString]['username'];
          if (winnerName == username){
            tempWinIds.add(game);
            int loserID = gameMap[gameIdString]['loser_id'];
            Map<String, dynamic> loserMap = await api.getUsername(loserID);
            String loserIdString = loserID.toString();
            String loserName = loserMap[loserIdString]['username'];
            gameMap['loser_id'] = loserName;
            gameMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameMap[gameIdString]['timestamp'] * 1000);
            winsList.add(gameMap);
          }
      }
    }
    // print(winsList);
    winIds = tempWinIds;
    return winsList;
  }

  Future<List<Map<String, dynamic>>> getLosses(String username) async {
    List<Map<String, dynamic>> lossesList = [];
    List<int> tempLossIds = [];

    if (gameIds != null){
      List<int> tempIds = gameIds ?? [];
      for (var game in tempIds){
        Map<String, dynamic> gameMap = await api.getGameInfo(game);
        String gameIdString = game.toString();
        var loserId = gameMap[gameIdString]?["loser_id"];
        Map<String, dynamic> loserMap = await api.getUsername(loserId);
        String loserIdString =  loserId.toString();
        String loserName = loserMap[loserIdString]['username'];
        if (loserName == username){
          tempLossIds.add(game);
          int winnerID = gameMap[gameIdString]['winner_id'];
          Map<String, dynamic> winnerMap = await api.getUsername(winnerID);
          String winnerIdString = winnerID.toString();
          String winnerName = winnerMap[winnerIdString]['username'];
          gameMap['winner_id'] = winnerName;
          gameMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameMap[gameIdString]['timestamp'] * 1000);
          lossesList.add(gameMap);
        }
      }
    }
    // print(winsList);
    lossIds = tempLossIds;
    return lossesList;
  }

  Future<List<Map<String, dynamic>>> getOpponents(String username) async {
    List<Map<String, dynamic>> opponentsMaps = [];

    if (gameIds != null) {
      List<int> tempIds = gameIds ?? [];
      for (var game in tempIds) {
        Map<String, dynamic> gameMap = await api.getGameInfo(game);
        String gameIdString = game.toString();
        var loserId = gameMap[gameIdString]?["loser_id"];
        Map<String, dynamic> loserMap = await api.getUsername(loserId);
        String loserIdString = loserId.toString();
        String loserName = loserMap[loserIdString]['username'];
        //user loses
        if (loserName == username) {
          int winnerID = gameMap[gameIdString]['winner_id'];
          Map<String, dynamic> winnerMap = await api.getUsername(winnerID);
          String winnerIdString = winnerID.toString();
          String winnerName = winnerMap[winnerIdString]['username'];
          gameMap['opponent_name'] = winnerName;
          gameMap['my_points'] =  gameMap[gameIdString]['loser_points'];
          gameMap['opp_points'] = gameMap[gameIdString]['winner_points'];
          gameMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameMap[gameIdString]['timestamp'] * 1000);
          opponentsMaps.add(gameMap);
        }
        //user wins
        else{
          gameMap['opponent_name'] = loserName;
          gameMap['my_points'] = gameMap[gameIdString]['winner_points'];
          gameMap['opp_points'] = gameMap[gameIdString]['loser_points'];
          gameMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameMap[gameIdString]['timestamp'] * 1000);
          opponentsMaps.add(gameMap);
        }
      }
    }

    return opponentsMaps;
  }

  Future<List<Map<String, dynamic>>> getSwingSpeeds(String username) async {
    List<Map<String, dynamic>> swingsList = [];

    if (gameIds != null){
      List<int> tempIds = gameIds ?? [];
      for (var game in tempIds){
        Map<String, dynamic> gameStatMap = await api.getGameStats(game, username);
        Map<String, dynamic> gameInfoMap = await api.getGameInfo(game);
        String gameIdString = game.toString();
        gameStatMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameInfoMap[gameIdString]['timestamp'] * 1000);
        swingsList.add(gameStatMap);
      }
    }

    return swingsList;
  }

  Widget winsListWidget(List<Map<String, dynamic>> winsList) {
    print("in widget");
    print("winsList length: ${winsList.length}");
    return Container(
      color: Theme.of(context).cardColor,
      child: ListView.builder(
        itemCount: winsList.length,
        itemBuilder: (context, index) {
          final win = winsList[index];
          print(win);
          return ListTile(
            title: Text("${win['date_time']} Opponent: ${win['loser_id']}"),
            subtitle: Text("Score: ${win[winIds?[index].toString()]['winner_points']} - ${win[winIds?[index].toString()]['loser_points']} Game Type: ${win[winIds?[index].toString()]['game_type']}"),
          );
        }
      ),
    );
  }

  Widget lossesListWidget(List<Map<String, dynamic>> lossesList) {
    print("in widget");
    print("lossesList length: ${lossesList.length}");
    return Container(
      color: Theme.of(context).cardColor,
      child: ListView.builder(
          itemCount: lossesList.length,
          itemBuilder: (context, index) {
            final loss = lossesList[index];
            print(loss);
            return ListTile(
              title: Text("${loss['date_time']} Opponent: ${loss['winner_id']}"),
              subtitle: Text("Score: ${loss[lossIds?[index].toString()]['winner_points']} - ${loss[lossIds?[index].toString()]['loser_points']} Game Type: ${loss[lossIds?[index].toString()]['game_type']}"),
            );
          }
      ),
    );
  }

  Widget oppsListWidget(List<Map<String, dynamic>> oppsList) {
    return Container(
      color: Theme.of(context).cardColor,
      child: ListView.builder(
          itemCount: oppsList.length,
          itemBuilder: (context, index) {
            final opp = oppsList[index];
            print(opp);
            return ListTile(
              title: Text("${opp['date_time']}: ${opp['opponent_name']}"),
              subtitle: Text("Me-Opponent: ${opp['my_points']} - ${opp['opp_points']} Game Type: ${opp[gameIds?[index].toString()]['game_type']}"),
            );
          }
      ),
    );
  }

  Widget swingSpeedWidget(List<Map<String, dynamic>> swingsList) {
    return Container(
      color: Theme.of(context).cardColor,
      child: ListView.builder(
          itemCount: swingsList.length,
          itemBuilder: (context, index) {
            final swing = swingsList[index];
            return ListTile(
              title: Text("${swing['date_time']} (unit)"),
              subtitle: Text("Average: ${swing[gameIds?[index].toString()]['swing_avg']} Min: ${swing[gameIds?[index].toString()]['swing_min']} Max: ${swing[gameIds?[index].toString()]['swing_max']}"),
            );
          }
      ),
    );
  }

  Widget errorWidget() => Center(child: Text('Choose a Stat'));

  Future<List<Map<String, dynamic>>> _getSelectedHistory(String username) async {
    if(selectedStat == "Wins"){
      // print("get wins");
      final wins = await getWins(username);
      // print(wins);
      return wins;
    }
    else if(selectedStat == "Losses"){
      print("get losses");
      final losses = await getLosses(username);
      return losses;
    }
    else if(selectedStat == "Opponents"){
      final opps = await getOpponents(username);
      return opps;
    }
    else if(selectedStat == "Swing Speeds"){
      final swings = await getSwingSpeeds(username);
      return swings;
    }
    else{
      print("can't get value: ${selectedStat}");
      return [];
    }

  }


  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('History'),
      ),
      body: Center(
        child: Column(
          children: [
            ValueListenableBuilder(
                valueListenable: internetConnection.isOnline,
                builder: (context, online, _){
                  print("Game Page Connectivity: $online");
                  return online ? Text("") : Text("Offline");
                }
            ),
            DropdownButton<String>(
                hint: Text("Select a stat to view"),
                value: selectedStat,
                onChanged: (String? newValue){
                  setState(() {
                    selectedStat = newValue;
                  });
                },
                items: statsToView.map((String value) {
                  return DropdownMenuItem<String>(
                      value: value,
                      child: Text(value)
                  );
                }).toList(),
            ),
            Expanded(
              child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _getSelectedHistory(context.read<User>().username),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return CircularProgressIndicator();
                    } else if (snapshot.hasError) {
                      return Text('Error: ${snapshot.error}');
                    } else {
                      final data = snapshot.data!;
                      print(data);
                      switch(selectedStat){
                        case "Wins":
                          return winsListWidget(data);
                        case "Losses":
                          return lossesListWidget(data);
                        case "Opponents":
                          return oppsListWidget(data);
                        case "Swing Speeds":
                          return swingSpeedWidget(data);
                        default:
                          return errorWidget();
                      }
                    }
                },
              ),
            )
          ],
        ),
      ),
    );
  }
}

class LoginPage extends StatefulWidget{
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final internetConenction = ConnectivityCheck();

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('Login or Create User'),
      ),
      body: Center(
        child: Column(
          children: [
            MyTextEntryWidget(),
            ValueListenableBuilder(
                valueListenable: internetConenction.isOnline,
                builder: (context, online, _){
                  print("Login Page Connectivity: $online");
                  return online ? Text("") : Text("Offline");
                }
            ),
          ],
        ),
      ),
    );
  }
}

class ProfilePage extends StatefulWidget{
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  bool isConnected = false;
  final internetConnection = ConnectivityCheck();

  void scan(){
    myBLE.startScan(onDeviceDiscovered: (device) {
      setState(() {}); // Trigger rebuild; myBLE.devices is already updated
    });
  }

  void connect(DiscoveredDevice device){
    print("Pressed");
    myBLE.connectDevice(device, (bool status) {
      setState(() {
        isConnected = status;
      });
      print("Connection status updated: $status");
    });

  }

  void initState() {
    super.initState();
    scan();
  }

  @override
  Widget build(BuildContext context){
    final List<DiscoveredDevice> devices = myBLE.devices;
    final user = context.read<User>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Profile'),
      ),
      body: Center(
        child: Column(
          children: [
            ValueListenableBuilder(
              valueListenable: internetConnection.isOnline,
              builder: (context, online, _){
                print("Game Page Connectivity: $online");
                return online ? Text("") : Text("Offline");
              }
            ),
            Container(
              width: 100,
              height: 100,
              child: Icon(
                  Icons.account_circle,
                  size: 72
              ),
            ),
            Text(
                "Hello, ${user.username}"
            ),
            SizedBox(height: 16,),
            Expanded(
              child: ListView.builder(
                  itemCount: devices.length,
                  itemBuilder: (context, index) {
                    final device = devices[index];
                    return ListTile(
                      title: Text(device.name.isNotEmpty ? device.name : "Unnamed"),
                      subtitle: Text(device.id),
                      //trailing: Text("RSSI: ${device.rssi}"),
                      onTap: () => connect(device),
                    );
                  }
              ),
            ),
            ElevatedButton(
                onPressed: scan,
                child: Text("Rescan")
            )
          ],
        ),
      ),
    );
  }
}