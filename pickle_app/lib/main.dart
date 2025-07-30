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
  //Hive local caching inits
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();
  await Hive.openBox('cacheBox'); //box where cached data will be stored

  //init a global user, any widgets using it will be notified on change
  runApp(ChangeNotifierProvider(
    create: (context) => User(username: "", gamesPlayed: 0, gamesWon: 0, avgScore: 0),
    child: MyApp(),));
}


///class holding all api requests to database
///generally only do communication, no data manipulation
class APIRequests {
  //current laptop IP address, change manually
  final String url = "http://10.6.24.241:80";

  ///get username, gamesPlayed, gamesWon, and averageScore from user id num
  Future<Map<String, dynamic>> getUserRequest(int id_num) async {
    //* all api calls follow this general setup

    //make a map with the param name from rest_api.md and the flutter value it should be assigned
    Map<String, int> u_id = {
      'user_id': id_num,
    };

    print(u_id);
    //the endpoint for the api to call in rest_api.md
    String endpoint = "/pickle/user/get";
    print("$endpoint");
    //NOTE Authorization header for authorization api (look up standard authorization header, Bearer)

    //create the response using http.post
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

    //check for a successful response
    if (response.statusCode == 200 || response.statusCode == 201){
      //if the response is successful return a Map<String, dynamic> in the returns format from rest_api.md
      return json.decode(response.body);
    }
    else{
      //if the response is not successful view a message with status code and the body that caused the error
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  ///create a new user in the database with given username and password
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

  ///get the user id number of a user given their username, useful for other calls
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

  ///get all of a user's friends indexed by id number - includes username, gamesPlayed, and winRate in returned map
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

  ///add a friend for a user to the database given both users' usernames
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

  ///confirm a user can login, return an apiKey for future use when running with authorization
  Future<String> authorizeLogin(String un, String pw) async {
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
        return responseData['apiKey'];
      }
    }
    return "";
  }

  ///save a completed game to the database
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

  Future<Map<String, dynamic>> registerStats(String un, int gameID, int swingCount, int swingHits, double swingMax) async{
    Map<String, dynamic> userId = await getUserID(un);
    final int userIdNum = userId[un];


    Map<String, dynamic> params = {
      'user_id': userIdNum,
      'game_id': gameID,
      'swing_count': swingCount,
      'swing_hits': swingHits,
      'swing_max': swingMax,
      'Q1_hits': 0,
      'Q2_hits': 0,
      'Q3_hits': 0,
      'Q4_hits': 0
    };

    print(params);
    String endpoint = "/pickle/game/registerStats";
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

  ///get a list of game id numbers the given user has participated in
  //TODO add sorting options (should just need add parameter, adjust params accordingly)
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

  ///get the timestamp, game type, winner id, loser id, winner points, loser points corresponding to a game id number
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

  ///get a variety of swing and git information for a user from a specified game
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

  ///get the username from a user's id number
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

//create a global singleton instance of the APIRequests class
final api = APIRequests();

///this class holds user information that is needed throughout the app
///when any values are changed all User widgets are notified
class User extends ChangeNotifier {
  String username;
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

  //***these json conversions should not be used
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

  ///update the global user to represent the specified user from the database
  Future<void> updateUserfromDatabase(String newUserName) async{

    newUserName = newUserName.trim();
    print("in updateUserfromDatabase");
    Map<String, dynamic> user_id = await api.getUserID(newUserName);

    final int id_num = user_id[newUserName];
    final String id_string = id_num.toString();

    Map<String, dynamic> newUserMap = await api.getUserRequest(id_num);
    Map<String, dynamic> userMap = newUserMap[id_string];

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

  ///reset the global user to "blank" values
  void resetUser(){
    username = "";
    gamesPlayed = 0;
    gamesWon = 0;
    avgScore = 0;
    pals = [];
    opponent = "";
  }
}

///class holding functions and values for BLE connection
class BleFunctionality{

  final FlutterReactiveBle flutterReactiveBle = FlutterReactiveBle(); //instantiate flutter ble class
  final List<DiscoveredDevice> devices = []; //devices found in scan
  late StreamSubscription<DiscoveredDevice> scanSubscription;
  late StreamSubscription<ConnectionStateUpdate> connection; //the established ble connection
  DiscoveredDevice? connectedDevice; //device that was connected to

  //notify the game page when new data is received
  final ValueNotifier<String?> latestScoreData = ValueNotifier(null);
  final ValueNotifier<String?> latestSwingData = ValueNotifier(null);

  BleFunctionality();

  ///get the needed permissions for ble functionality on android
  Future<bool> requestPermissions() async {
    final status = await [
      Permission.location,
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
    ].request();

    return status.values.every((s) => s.isGranted);
  }

  ///scan for ble devices when permissions are granted
  Future<void> startScan({required void Function(DiscoveredDevice) onDeviceDiscovered}) async {
    //wait for permissions to be granted
    bool granted = await requestPermissions();
    if(granted) {
      //listen for ready ble devices
      flutterReactiveBle.statusStream.listen((status) {
        if (status == BleStatus.ready) {
          print("Ready for BLE discovery");
          scanSubscription = flutterReactiveBle
              .scanForDevices(withServices: <Uuid>[])
              .listen((device) {
            //add device if not already in list
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

  ///connect to the selected ble status
  Future<void> connectDevice(DiscoveredDevice selectedDevice, void Function(bool) connectionStatus) async {
    //try connecting to the device
    connection = flutterReactiveBle.connectToDevice(id: selectedDevice.id).listen((connectionState) {
      print("Connection State for device ${selectedDevice
          .name} : ${connectionState.connectionState}");
      if (connectionState.connectionState == DeviceConnectionState.connected) {
        //on a connection call callback with true, set connected device
        connectionStatus(true);
        connectedDevice = selectedDevice;
        print("connected");
      }
      else if (connectionState.connectionState ==
          DeviceConnectionState.disconnected) {
        //on a connection call callback with false, no connected device
        connectionStatus(false);
        connectedDevice = null;
        print("disconnected");
      }
    }, onError: (Object error){
      print("Connecting to device resulted in error $error");
    });
  }

  ///subscribe to characteristic with a connected device and necessary uuids
  //TODO edit for use with other characteristics, likely make two other functions
  void readScoreLiveFromDevice({
    required DiscoveredDevice connectedDevice,
  }){

    final serviceUuid = Uuid.parse("6c914f48-d292-4d61-a197-d4d5500b60cc");
    final scoreCharUuid = Uuid.parse("27923275-9745-4b89-b6b2-a59aa7533495");

    print("in readLiveFromDevice");
    final characteristic = QualifiedCharacteristic(
        characteristicId: scoreCharUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice.id);

    flutterReactiveBle.subscribeToCharacteristic(characteristic).listen((data) {
      final value = utf8.decode(data); //get decoded value
      print("Received from BLE: $value");
      latestScoreData.value = value; //update latestData value
    }, onError: (error) {
      latestScoreData.value = null;
      print("Error subscribing to notifications: $error");
    });
  }

  void readSwingLiveFromDevice({
    required DiscoveredDevice connectedDevice,
  }){

    final serviceUuid = Uuid.parse("6c914f48-d292-4d61-a197-d4d5500b60cc");
    final maxSwingCharUuid = Uuid.parse("8b2c1a45-7d3e-4f89-a2b1-c5d6e7f8a9b0");

    print("in readLiveFromDevice");
    final characteristic = QualifiedCharacteristic(
        characteristicId: maxSwingCharUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice.id);

    flutterReactiveBle.subscribeToCharacteristic(characteristic).listen((data) {
      final value = utf8.decode(data); //get decoded value
      print("Received from BLE: $value");
      latestSwingData.value = value; //update latestData value
    }, onError: (error) {
      latestSwingData.value = null;
      print("Error subscribing to notifications: $error");
    });
  }

  void writeReset() async{
    final serviceUuid = Uuid.parse("6c914f48-d292-4d61-a197-d4d5500b60cc");
    final scoreCharUuid = Uuid.parse("27923275-9745-4b89-b6b2-a59aa7533495");

    print("in writeReset");
    final characteristic = QualifiedCharacteristic(
        characteristicId: scoreCharUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice!.id);

    //convert the reset message into bytes to be sent
    String resetMessage = "RESET";
    List<int> resetInBytes = resetMessage.codeUnits;

    await flutterReactiveBle.writeCharacteristicWithoutResponse(
        characteristic,
        value: resetInBytes
    );

  }
  ///stop scanning when leaving profile page
  void stopScan() {
    scanSubscription.cancel();
    print("Scan stopped");
  }
}

//create a global singleton instance of the BLE class
final myBLE = BleFunctionality();

///class holding values and functions for games
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

  int swingCount = 0;
  int swingHits = 0;
  double swingMax = 0;



  void newSwing(double swingSpeed){
    swingCount+=1;
    print("swing count $swingCount");

    if(swingCount == 0 || swingSpeed > swingMax){
      swingMax = swingSpeed;
      print("new max speed: $swingMax");
    }
  }

  void incMyScore(){
    myScore += 1;
  }

  void incOppScore(){
    opponentScore += 1;
  }

  ///true if a player has a score of at least 11 and is winning by at least 2
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

  ///if there is a winner, the player with the higher score is the winner
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

  ///convert the String gameType to a int value
  //are going to keep one standard game
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

///class to check for network connection
class ConnectivityCheck {
  //only allow for one instance
  static final ConnectivityCheck _instance = ConnectivityCheck._internal();
  factory ConnectivityCheck() => _instance;
  ConnectivityCheck._internal(){
    _init();
  }

  //init library
  final _connectivity = Connectivity();
  final ValueNotifier<bool> isOnline = ValueNotifier(true);

  ///get initial connection and double check
  void _init() async{
    await _checkInitStatus();

    _connectivity.onConnectivityChanged.listen((result){
      final online = !result.contains(ConnectivityResult.none);
      isOnline.value = online;
    });

  }

  ///get initial connection status
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

  ///listen for a restored connection, then send previously cached data to database
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

///widget for logging in
///TODO Rename
class MyTextEntryWidget extends StatefulWidget {
  @override
  _MyTextEntryWidgetState createState() => _MyTextEntryWidgetState();
}

class _MyTextEntryWidgetState extends State<MyTextEntryWidget> {
  //controller variables describing the text entries
  final TextEditingController _controller1 = TextEditingController();
  final TextEditingController _controller2 = TextEditingController();

  //TODO add back create user on login page
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

  ///check for valid username and password with database then go to home
  _login(String userName, String password) async {
    String apiKey = await api.authorizeLogin(userName, password);

    print("LOGIN UN: $userName");

    if(apiKey != ""){
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
            controller: _controller1, //username entry is controlled by controller1
            decoration: InputDecoration(
              labelText: 'Enter username',
              border: OutlineInputBorder(),
            ),
          ),
          SizedBox(
            height: 16,
          ),
          TextField(
            controller: _controller2, //password is controlled by controller2
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

///Top level widget
class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PicklePals',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.tealAccent),
        scaffoldBackgroundColor: Colors.white,
      ),
      initialRoute: '/', // Start at Login
      routes: { //used for forcing navigation without nav bar
        '/': (context) => LoginPage(),
        '/home': (context) => MyHomePage(),
        '/game': (context) => GamePage(),
      },
    );
  }
}

///Holds all pages except Login and navigation between them
class MyHomePage extends StatefulWidget {
  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {

  //page selected in nav bar
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

///Page where game can be viewed/played
class GamePage extends StatefulWidget{
  const GamePage({super.key});

  @override
  State<GamePage> createState() => _GamePageState();
}

class _GamePageState extends State<GamePage> {
  var game = Game();
  bool isLoading = true;
  final internetConnection = ConnectivityCheck(); //check for internet connection
  late VoidCallback _bleDataListener; //function for receiving new data from ble
  late VoidCallback _bleSwingSpeedListener;

  ///check if the user has inputted an opponent and update game
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

  ///check game status to determine how the page title should appear
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

  ///mark that game has started
  void startStandardGame(){
    setState(() {
      game.startGame();
    });
    print("game started");
  }

  ///check internet connection to show and how game will be saved
  String showWinnerContent(String winnerName) {
    if(internetConnection.isOnline.value == true){
      return "$winnerName is the winner!";
    }
    else{
      return "$winnerName is the winner!\nData will be saved locally until connection is restored";
    }
  }

  ///display a popup with the winner, game save message, and save/restart button
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

  ///increase my score in game and check for winner
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

  ///increase opponent score in game and check for winner
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

  ///save finished game data to Hive box
  Future<void> cacheGame(int startTime, int gameTypeNum, String winnerName, String loserName, int winnerPoints, int loserPoints, String un, int swingCount, int swingHits, double swingMax) async {
    Map<String, dynamic> gameToSave = {
      'timestamp': startTime,
      'game_type': gameTypeNum,
      'winner_name': winnerName,
      'loser_name': loserName,
      'winner_points': winnerPoints,
      'loser_points': loserPoints,
      'username': un,
      //'game_id': gameId, will not be known on call
      'swing_count': swingCount,
      'swing_hits': swingHits,
      'swing_max': swingMax
    };

    final cacheBox = await Hive.openBox("gameQueue");
    await cacheBox.add(gameToSave);

  }

  ///open the Hive box and register each game in the queue to the database
  void sendCachedGames() async {
    final cacheBox = await Hive.openBox("gameQueue");
    final cacheBoxKeys = cacheBox.keys.toList();

    for(final key in cacheBoxKeys){
      final gameData = cacheBox.get(key);
      print(gameData);
      Map<String, dynamic> gameIdMap = await api.registerGame(gameData['timestamp'], gameData['game_type'], gameData['winner_name'], gameData['loser_name'], gameData['winner_points'], gameData['loser_points']);
      int gameID = gameIdMap['game_id'];
      api.registerStats(gameData['username'], gameID, gameData['swing_count'], gameData['swing_hits'], gameData['swing_max']);
    }
  }

  ///format game info for saving, cache or register to database, reset game
  void saveAndRestartGame() async{
    int gameTypeNum = game.gameTypeToInt();

    String winnerName = "";
    String loserName = "";

    int winnerPoints = -1;
    int loserPoints = -1;

    //handle no registered opponent
    if (game.opponentName == "Opponent"){
      //eventually change to NULL user
      game.opponentName = "testUser"; //TODO change to anonymous user
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
      Map<String, dynamic> gameIdMap = await api.registerGame(game.startTime, gameTypeNum, winnerName, loserName, winnerPoints, loserPoints);
      int gameID = gameIdMap['game_id'];
      String un = context.read<User>().username;
      api.registerStats(un, gameID, game.swingCount, game.swingHits, game.swingMax);
      myBLE.writeReset();
      print("Online. Sending game to database $un");
    }
    else{
      //TODO test game stat caching, BLE disconnected with wifi(could be bc app is sent to background when setting airplane mode, can turn wifi mode off on esp)
      //try just turning off wifi instead of full airplane mode
      cacheGame(game.startTime, gameTypeNum, winnerName, loserName, winnerPoints, loserPoints, context.read<User>().username, game.swingCount, game.swingHits, game.swingMax);
      print("Offline. Caching game data");
    }


    context.read<User>().setOpponent("");

    setState(() {
      game.resetGame();
    });
  }


  ///handle exiting page
  @override
  void dispose() {
    myBLE.latestScoreData.removeListener(_bleDataListener);
    myBLE.latestSwingData.removeListener(_bleSwingSpeedListener);
    super.dispose();
  }

  ///when the page is first built, or rebuilt for listener
  @override
  void initState() {
    super.initState();
    loadOpponent(); //get opponent name

    print("init game page");
    //listen for a new ble data value, update game and ui
    int prevMyButtonScore = 0;
    int prevOppButtonScore = 0;
    _bleDataListener = () {
      if (!mounted) return;
      final data = myBLE.latestScoreData.value;
      if (data != null) { //new data has been received and a game has been started
        int commaIdx = data.indexOf(',');
        int length = data.length;
        String myButtonScoreChar = data.substring(0, commaIdx);
        print("my score char $myButtonScoreChar");
        String oppButtonScoreChar = data.substring(commaIdx + 1, length);
        print("opp score char $oppButtonScoreChar");
        int myButtonScore = 0;
        int oppButtonScore = 0;
        try{
          myButtonScore = int.parse(myButtonScoreChar);
        }catch(e){
          print("error converting my button score to int $e");
        }
        try{
          oppButtonScore = int.parse(oppButtonScoreChar);
        }catch(e){
          print("error converting opp button score to int $e");
        }

        if(game.inProgress){
          print("Game in progress: ${game.inProgress}");
          if(myButtonScore - 1!= prevMyButtonScore){ //MY SCORE BUTTON MUST BE START
            setState(() {
              print("New data in GamePage: $data");
              incMyScore();
              print("My score: ${game.myScore}");
            });
            prevMyButtonScore = myButtonScore - 1;
          }
          if(oppButtonScore != prevOppButtonScore){
            setState(() {
              print("New data in GamePage: $data");
              incOppScore();
              print("Opponent score: ${game.opponentScore}");
            });
            prevOppButtonScore = oppButtonScore;
          }

        }
        else{
          startStandardGame();
        }
      }
    };

    //use the listener function to handle new ble data
    myBLE.latestScoreData.addListener(_bleDataListener);
    _bleSwingSpeedListener = () {
      if (!mounted) return;
      final data = myBLE.latestSwingData.value;
      if (data != null) { //new data has been received and a game has been started
        if (game.inProgress) {
          print("Game in progress: ${game.inProgress}");
          setState(() {
            print("New data in GamePage: $data");
            try {
              //convert received string to double
              String dataNumbersParse = data.replaceAll(" m/s", "");
              double dataNum = double.parse(dataNumbersParse);
              game.newSwing(dataNum);
            } catch (e) {
              print("error converting swing data to double: $e");
            }
          });
        } else {
          print("swing will not count until game is started");
        }
      }
    };

    myBLE.latestSwingData.addListener(_bleSwingSpeedListener);

    //when internet connection is restored, immediately send cached games to database
    internetConnection.connectionRestoreListener((){
      print("Internet connection restored. Sending cached games");
      sendCachedGames();
    });

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
                //dont show message unless offline
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
              SizedBox(width: 70,),
              Flexible(
                child: Text(
                  game.opponentName,
                  style: TextStyle(
                      fontSize: 24
                  ),
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

///Page to view and interact with friends
class SocialPage extends StatefulWidget{
  const SocialPage({super.key});

  @override
  State<SocialPage> createState() => _SocialPageState();
}

class _SocialPageState extends State<SocialPage> {
  //controller for friend username text entry
  final TextEditingController _controller = TextEditingController();
  bool isLoading = true;
  //check for internet connection
  final internetConnection = ConnectivityCheck();

  ///everytime the page is built
  @override
  void initState() {
    super.initState();
    //refresh user info
    loadUser();
  }

  ///refresh user everytime the page is built to keep friends updated
  Future<void> loadUser() async {
    final username = context.read<User>().username;
    await context.read<User>().updateUserfromDatabase(username);
    setState(() {
      isLoading = false;
    });
  }

  ///testing function to print all friend names of a user
  Future<void> showFriends(String username) async{
    try{
      var friends = await api.getFriends(username);
      print("Friends: $friends");
      print(friends.runtimeType);
    } catch(e){
      print("error getting friends: $e");
    }
  }

  ///add a friend for a user and update that user
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

  ///give a friend as an opponent and update user
  void startGameWithPal(String palName){
    print("Start game with $palName");
    context.read<User>().setOpponent(palName);
  }

  ///show a popup to start a game with a friend, delete a friend, or cancel
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
                  //only show message when offline
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
              child: ListView.builder( //list of a user's friends and their info
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

///page to view history of a selected stat in a list
class HistoryPage extends StatefulWidget{
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  //options in dropdown
  List<String> statsToView = ["Wins", "Losses", "Opponents", "Points Scored", "Swing Speeds", "Hit Locations"];
  //option selected in dropdown
  String? selectedStat;
  //list of retrieved game ids
  List<int>? gameIds;
  //list of game ids resulting in wins
  List<int>? winIds;
  //list of games ids resulting in losses
  List<int>? lossIds;
  //check for internet connection
  final internetConnection = ConnectivityCheck();

  @override
  void initState() {
    super.initState();
    //once ui is built, load api calls and context to get games history
    WidgetsBinding.instance.addPostFrameCallback((_) => loadGamesHistory());
  }

  ///get all the games of the logged in user from database
  Future<void> loadGamesHistory() async {
    final currentUsername = context.read<User>().username;
    final data = await api.getUsersGames(currentUsername);

    //save the game ids as a list of ints
    List<dynamic> gameIdDynamic = data['game_ids'] ?? [];
    List<int> gameIdNums = gameIdDynamic.cast<int>();

    //check the widget is mounted before saving state
    if (mounted) {
      setState(() {
        gameIds = gameIdNums;
      });
    }
  }

  ///loop through game ids to check for wins for history list
  Future<List<Map<String, dynamic>>> getWins(String username) async {
    List<Map<String, dynamic>> winsList = [];
    List<int> tempWinIds = [];

    if (gameIds != null){
      //game ids is not empty, so temp is equal to game ids, if error blank list
      List<int> tempIds = gameIds ?? [];
      //loop through each game
      for (var game in tempIds){
        //get the game information
        Map<String, dynamic> gameMap = await api.getGameInfo(game);
        print(gameMap);
        String gameIdString = game.toString();
        //use the winner id to find the username of the winner
        var winnerId = gameMap[gameIdString]?["winner_id"];
        Map<String, dynamic> winnerMap = await api.getUsername(winnerId);
        String winnerIdString =  winnerId.toString();
        String winnerName = winnerMap[winnerIdString]['username'];
        //check if the user is the winner
        if (winnerName == username){
          //the user is the winner so save id
          tempWinIds.add(game);
          //get the loser id and username
          int loserID = gameMap[gameIdString]['loser_id'];
          Map<String, dynamic> loserMap = await api.getUsername(loserID);
          String loserIdString = loserID.toString();
          String loserName = loserMap[loserIdString]['username'];
          //change loser id locally to be better for ui
          gameMap['loser_id'] = loserName;
          //add date_time to format unix timestamp better for ui
          gameMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameMap[gameIdString]['timestamp'] * 1000);
          winsList.add(gameMap);
        }
      }
    }
    //set winIds
    winIds = tempWinIds;
    return winsList;
  }

  ///loop through game ids to check for losses for history list
  Future<List<Map<String, dynamic>>> getLosses(String username) async {
    List<Map<String, dynamic>> lossesList = [];
    List<int> tempLossIds = [];

    if (gameIds != null){
      //game ids is not empty, so temp is equal to game ids, if error blank list
      List<int> tempIds = gameIds ?? [];
      //loop through games
      for (var game in tempIds){
        //get the game information
        Map<String, dynamic> gameMap = await api.getGameInfo(game);
        String gameIdString = game.toString();
        //user the loser id to get the loser name
        var loserId = gameMap[gameIdString]?["loser_id"];
        Map<String, dynamic> loserMap = await api.getUsername(loserId);
        String loserIdString =  loserId.toString();
        String loserName = loserMap[loserIdString]['username'];
        //check if user is the loser
        if (loserName == username){
          //user is the loser so add game to list of loss ids
          tempLossIds.add(game);
          //user winner id to get winner name
          int winnerID = gameMap[gameIdString]['winner_id'];
          Map<String, dynamic> winnerMap = await api.getUsername(winnerID);
          String winnerIdString = winnerID.toString();
          String winnerName = winnerMap[winnerIdString]['username'];
          //replace winner id with winner name locally to better suit ui
          gameMap['winner_id'] = winnerName;
          //add date_time to format unix timestamp better for ui
          gameMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameMap[gameIdString]['timestamp'] * 1000);
          lossesList.add(gameMap);
        }
      }
    }


    lossIds = tempLossIds;
    return lossesList;
  }

  ///loop through games to find opponent names for history list
  Future<List<Map<String, dynamic>>> getOpponents(String username) async {
    List<Map<String, dynamic>> opponentsMaps = [];

    if (gameIds != null) {
      List<int> tempIds = gameIds ?? [];
      //loop through games
      for (var game in tempIds) {
        //get game info
        Map<String, dynamic> gameMap = await api.getGameInfo(game);
        String gameIdString = game.toString();
        //use loser id to get loser name
        var loserId = gameMap[gameIdString]?["loser_id"];
        Map<String, dynamic> loserMap = await api.getUsername(loserId);
        String loserIdString = loserId.toString();
        String loserName = loserMap[loserIdString]['username'];
        //user loses
        if (loserName == username) {
          //use winner id to get opponent name
          int winnerID = gameMap[gameIdString]['winner_id'];
          Map<String, dynamic> winnerMap = await api.getUsername(winnerID);
          String winnerIdString = winnerID.toString();
          String winnerName = winnerMap[winnerIdString]['username'];
          //update game map to better display info
          gameMap['opponent_name'] = winnerName;
          gameMap['my_points'] =  gameMap[gameIdString]['loser_points'];
          gameMap['opp_points'] = gameMap[gameIdString]['winner_points'];
          gameMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameMap[gameIdString]['timestamp'] * 1000);
          opponentsMaps.add(gameMap);
        }
        //user wins
        else{
          //opponent name is already known
          //update game map to better display info
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

  //TODO finish stat history implementation
  //similar layout to others, this function should be done, but needs tested
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

  ///display the list of wins
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

  ///display the list of losses
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

  ///display the list of opponents
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

  ///display list of swing speeds
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

  ///display error message
  Widget errorWidget() => Center(child: Text('Choose a Stat'));

  ///get the necessary data depending on what stat is selected in dropdown
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
                  //only display if offline
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
                  if (snapshot.connectionState == ConnectionState.waiting) { //get selected data
                    return CircularProgressIndicator();
                  } else if (snapshot.hasError) {
                    return Text('Error: ${snapshot.error}');
                  } else { //display corresponding widget with loaded data
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

///page where user logs in
//TODO create user saving option, look at Michael's new code
class LoginPage extends StatefulWidget{
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  //check for internet connection
  final internetConnection = ConnectivityCheck();
  //corresponds to selection of checkbox where user can save login
  bool saveChecked = false;

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('Login or Create User'),
      ),
      body: Center(
        child: Column(
          children: [
            MyTextEntryWidget(), //widget holding text entries and button
            ValueListenableBuilder(
                valueListenable: internetConnection.isOnline,
                builder: (context, online, _){
                  //only display message is offline
                  return online ? Text("") : Text("Offline");
                }
            ),
            SizedBox(height: 32,),
            Row(
              children: [
                SizedBox(width: 20,),
                Text("Would you like to save this user?"),
                Checkbox(
                    value: saveChecked,
                    onChanged: (bool ? newValue) {
                      setState(() {
                        saveChecked = newValue!;
                      });
                    }
                )
              ],
            ),

          ],
        ),
      ),
    );
  }
}

///page where user can connect to ble device and logout
class ProfilePage extends StatefulWidget{
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  //check internet connection
  final internetConnection = ConnectivityCheck();
  //ble service uuid

  ///calls ble function to scan for discoverable ble devices
  void scan(){
    myBLE.startScan(onDeviceDiscovered: (device) {
      setState(() {}); //does not work without setState
    });
    print("scan pressed");
  }

  ///calls ble connect function for the selected device and begins subscription
  void connect(DiscoveredDevice device){
    print("Pressed");
    myBLE.connectDevice(device, (bool status) {
      //check for widget mounting issues to avoid crashed
      if(!mounted) return;

      print("Connection status updated: $status");

      //device is connected so begin subscription to characteristic
      if(status){
        myBLE.readScoreLiveFromDevice(connectedDevice: device);
        myBLE.readSwingLiveFromDevice(connectedDevice: device);
      }
      else{
        print("Ble connection failed");
      }
    });

  }

  ///user logout by resetting global user
  void logout(){
    Provider.of<User>(context, listen: false).resetUser();
  }

  ///scan for devices on every page build
  void initState() {
    super.initState();
    scan();
  }

  ///quit scanning when leaving the page
  @override
  void dispose() {
    myBLE.stopScan();
    super.dispose();
  }

  @override
  Widget build(BuildContext context){
    //list of all devices from scan
    final List<DiscoveredDevice> devices = myBLE.devices;
    //local copy of global user
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
                  //only display message when offline
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
            ElevatedButton( //reset user and return to login page on logout
                onPressed: () {
                  logout();
                  Navigator.pushReplacementNamed(context, '/');
                },
                child: Text("Logout")
            ),
            Expanded(
              child: ListView.builder(
                  itemCount: devices.length,
                  itemBuilder: (context, index) {
                    final device = devices[index];
                    return ListTile(
                      title: Text(device.name.isNotEmpty ? device.name : "Unnamed"),
                      subtitle: Text(device.id),
                      onTap: () => connect(device),
                    );
                  }
              ),
            ),
            ElevatedButton(
                onPressed: scan, //does not seem to work
                child: Text("Rescan")
            )
          ],
        ),
      ),
    );
  }
}