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
  final String url = "http://10.6.31.66:80";
  String apiToken = "";

  ///get username, gamesPlayed, gamesWon, and averageScore from user id num
  Future<Map<String, dynamic>> getUserRequest(int id_num) async {
    //* all api calls follow this general setup

    //make a map with the param name from rest_api.md and the flutter value it should be assigned
    Map<String, int> u_id = {
      'user_id': id_num,
    };

    print(u_id);
    //the endpoint for the api to call in rest_api.md
    String endpoint = "/pickle/user/getStats";
    print("$endpoint");
    //NOTE Authorization header for authorization api (look up standard authorization header, Bearer)

    //create the response using http.post
    final response = await http.post(
        Uri.parse('$url$endpoint'),
        headers: {
          'Content-Type': 'application/json',
          "Authorization": "Bearer $apiToken",
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
        "Authorization": "Bearer $apiToken",
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
        "Authorization": "Bearer $apiToken",
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
        "Authorization": "Bearer $apiToken",
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
        "Authorization": "Bearer $apiToken",
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

    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(params),
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
    int winner_id_num = -1;
    int loser_id_num = -1;

    if(winnerName != "Opponent"){
      Map<String, dynamic> winner_id = await getUserID(winnerName);
      winner_id_num = winner_id[winnerName];
    }
    if(loserName != "Opponent"){
      Map<String, dynamic> loser_id = await getUserID(loserName);
      loser_id_num = loser_id[loserName];
    }

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
        "Authorization": "Bearer $apiToken",
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

  ///save stats from a completed game to the database
  Future<Map<String, dynamic>> registerStats(String un, int gameID, int swingCount, int swingHits, double swingMax, int q1, int q2, int q3, int q4) async{
    Map<String, dynamic> userId = await getUserID(un);
    final int userIdNum = userId[un];


    Map<String, dynamic> params = {
      'user_id': userIdNum,
      'game_id': gameID,
      'swing_count': swingCount,
      'swing_hits': swingHits,
      'swing_max': swingMax,
      'Q1_hits': q1,
      'Q2_hits': q2,
      'Q3_hits': q3,
      'Q4_hits': q4
    };

    print(params);
    String endpoint = "/pickle/game/registerStats";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        "Authorization": "Bearer $apiToken",
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
        "Authorization": "Bearer $apiToken",
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
        "Authorization": "Bearer $apiToken",
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

  ///get a variety of swing and hit information for a user from a specified game
  Future<Map<String, dynamic>> getGameStats(int gameID, String un) async {
    Map<String, dynamic> user_id = await getUserID(un);
    final int user_id_num = user_id[un];
    //games generated from database_setup.py may not have generated simulated stats
    //check for gameID of a game generated by app usage, not setup
    if(gameID >= 231754234702){
      //send as usual
      Map<String, dynamic> params = {
        'user_id' : user_id_num,
        'game_id': gameID
      };

      print(params);
      String endpoint = "/pickle/game/stats";
      print("$endpoint");


      final response = await http.post(
        Uri.parse('$url$endpoint'),
        headers: {
          'Content-Type': 'application/json',
          "Authorization": "Bearer $apiToken",
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
    else{
      //the game was generated by setup, create default stats to show with the game
      print("game not in range to get stats, returning default");
      String gameIdString = gameID.toString();
      Map<String, dynamic> defaultGameStats = {
        gameIdString : {
          "timestamp": 0,
          "swing_count": 0,
          "swing_hits": 0,
          "hit_percentage": 0.0,
          "swing_min": 0.0,
          "swing_max": 0.0,
          "swing_avg": 0.0,
          "hit_modeX": 0.0,
          "hit_modeY": 0.0,
          "hit_avgX": 0.0,
          "hit_avgY": 0.0,
        }
      };
      defaultGameStats['date_time'] = DateTime.fromMillisecondsSinceEpoch(defaultGameStats[gameIdString]['timestamp'] * 1000);
      return defaultGameStats;
    }

  }

  ///get the username from a user's id number
  Future<Map<String, dynamic>> getUsername(int userId) async {

    Map<String, dynamic> params = {
      'user_id': userId,
    };

    print(params);
    String endpoint = "/pickle/user/getUsername";
    print("$endpoint");


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        "Authorization": "Bearer $apiToken",
      },
      body: json.encode(params),
    );

    print("Sent JSON: ${jsonEncode(params)}");
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
    print("User id map: $user_id");

    final int id_num = user_id[newUserName];
    final String id_string = id_num.toString();

    Map<String, dynamic> newUserMap = await api.getUserRequest(id_num);
    Map<String, dynamic> userMap = newUserMap[id_string];

    Map<String,dynamic> usernameMap = await api.getUsername(id_num);
    print("USERNAME MAP: $usernameMap");

    Map<String, dynamic> friendMap = await api.getFriends(newUserName);

    List<Map<String, dynamic>> friendList = [];

    friendMap.forEach((id, data) {
      friendList.add(data);
    });

    username = usernameMap[id_string];
    gamesPlayed = userMap['gamesPlayed'];
    gamesWon = userMap['gamesWon'];
    avgScore = userMap['averageScore'];
    pals = friendList;

    notifyListeners();//update all widgets using user info
  }

  void setOpponent(String opponentName){
    opponent = opponentName;
    notifyListeners();
  }

  void setPals(List<Map<String,dynamic>> newPalsList){
    pals = newPalsList;
    notifyListeners();
  }

  ///offline mode, reset the user and set username
  void setCacheUser(String un){
    resetUser();
    username = un;
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
  late StreamSubscription<DiscoveredDevice> scanSubscription; //scanning
  late StreamSubscription<ConnectionStateUpdate> connection; //the established ble connection
  DiscoveredDevice? connectedDevice; //device that was connected to

  //notify the game page when new data is received from paddle
  final ValueNotifier<String?> latestScoreData = ValueNotifier(null);
  final ValueNotifier<String?> latestSwingData = ValueNotifier(null);
  final ValueNotifier<String?> latestHitData = ValueNotifier(null);

  BleFunctionality(); //instantiate library

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
    print("trying to connect to device");
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
  void readScoreLiveFromDevice({
    required DiscoveredDevice connectedDevice,
  }){

    final serviceUuid = Uuid.parse("6c914f48-d292-4d61-a197-d4d5500b60cc");
    final scoreCharUuid = Uuid.parse("27923275-9745-4b89-b6b2-a59aa7533495");

    print("in readScoreLiveFromDevice");
    final characteristic = QualifiedCharacteristic(
        characteristicId: scoreCharUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice.id);

    flutterReactiveBle.subscribeToCharacteristic(characteristic).listen((data) {
      final value = utf8.decode(data); //get decoded value
      //print("Received from BLE: $value");
      latestScoreData.value = value; //update latestData value
    }, onError: (error) {
      latestScoreData.value = null;
      print("Error subscribing to notifications: $error");
    });
  }

  ///subscribe to swing characteristic
  void readSwingLiveFromDevice({
    required DiscoveredDevice connectedDevice,
  }){

    final serviceUuid = Uuid.parse("6c914f48-d292-4d61-a197-d4d5500b60cc");
    final maxSwingCharUuid = Uuid.parse("8b2c1a45-7d3e-4f89-a2b1-c5d6e7f8a9b0");

    print("in readSwingLiveFromDevice");
    final characteristic = QualifiedCharacteristic(
        characteristicId: maxSwingCharUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice.id);

    flutterReactiveBle.subscribeToCharacteristic(characteristic).listen((data) {
      final value = utf8.decode(data); //get decoded value
      // print("Received from BLE: $value");
      latestSwingData.value = value; //update latestData value
    }, onError: (error) {
      latestSwingData.value = null;
      print("Error subscribing to notifications: $error");
    });
  }

  ///subscribe to hits characteristic
  void readHitsLiveFromDevice({
    required DiscoveredDevice connectedDevice,
  }){

    final serviceUuid = Uuid.parse("6c914f48-d292-4d61-a197-d4d5500b60cc");
    final hitCharUuid = Uuid.parse("9c3d2b56-8e4f-5a90-b3c2-d6e7f8a9b0c1");

    print("in readHitsLiveFromDevice");
    final characteristic = QualifiedCharacteristic(
        characteristicId: hitCharUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice.id);

    flutterReactiveBle.subscribeToCharacteristic(characteristic).listen((data) {
      final value = utf8.decode(data); //get decoded value
      // print("Received from BLE: $value");
      latestHitData.value = value; //update latestData value
    }, onError: (error) {
      latestHitData.value = null;
      print("Error subscribing to notifications: $error");
    });
  }

  ///write to the score characteristic to reset values
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

  ///disconnect function, broken
  void disconnect(){
    connection.cancel();
    connectedDevice = null;
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
  int q1Hits = 0;
  int q2Hits = 0;
  int q3Hits = 0;
  int q4Hits = 0;

  ///update swing values when a new swing is detected
  void newSwing(double swingSpeed){
    swingCount+=1;
    print("swing count $swingCount");

    if(swingCount == 0 || swingSpeed > swingMax){
      swingMax = swingSpeed;
      print("new max speed: $swingMax");
    }
  }

  ///update hit values when a new hit is received
  void newHit(int q1, int q2, int q3, int q4){
    print("new hit");
    swingHits += 1;

    q1Hits = q1;
    q2Hits = q2;
    q3Hits = q3;
    q4Hits = q4;
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
    else if(opponentScore >= 15 || myScore >= 15){
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

    swingCount = 0;
    swingHits = 0;
    swingMax = 0;
    q1Hits = 0;
    q2Hits = 0;
    q3Hits = 0;
    q4Hits = 0;
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
  // creates a singleton that can be accessed by all four pages
  static final ConnectivityCheck _instance = ConnectivityCheck._internal();
  factory ConnectivityCheck() => _instance;
  ConnectivityCheck._internal() {
    _init();
  }

  //instantiate library
  final Connectivity _connectivity = Connectivity();
  //create a notifier for pages to see online status
  final ValueNotifier<bool> isOnline = ValueNotifier(true);
  //track previous state to try
  bool wasOffline = false;
  //debounce timer to try to avoid flooding the database when reconnecting
  Timer? debounceTimer;

  //callback function for when connection is restored
  VoidCallback? onReconnectCallback;

  void _init() async {
    await _checkInitStatus();

    //listen to see if connectivity status has changed
    _connectivity.onConnectivityChanged.listen((result) {
      final online = !result.contains(ConnectivityResult.none);
      isOnline.value = online;

      //if connection is restored after being online called reconnect handler
      if (online && wasOffline) {
        triggerOnReconnect();
      }

      //reset state
      wasOffline = !online;
    });
  }

  Future<void> _checkInitStatus() async {
    final result = await _connectivity.checkConnectivity();
    final online = !result.contains(ConnectivityResult.none);
    isOnline.value = online;
    wasOffline = !online;

    print('Initial connectivity: $result');
    //again to avoid rapid tasks, try waiting
    Future.microtask(() {
      print('isOnline after update: ${isOnline.value}');
    });
  }

  ///keep from sending reconnection requests too quickly when connection is being turned on and off
  void triggerOnReconnect() {
    //check if timer value is null, also if its running cancel it
    if (debounceTimer?.isActive ?? false) debounceTimer?.cancel();

    //wait for two seconds for signal to stabilize and call callback (send cached data)
    debounceTimer = Timer(const Duration(seconds: 2), () {
      if (onReconnectCallback != null) {
        print("connection restored. sending cached games");
        onReconnectCallback!();
      }
    });
  }

  ///called once to listen for restored connections and send cached data
  void connectionRestoreListener(VoidCallback sendCachedData) {
    onReconnectCallback = sendCachedData;
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
  late VoidCallback _bleDataListener; //function for receiving score data from ble
  late VoidCallback _bleSwingSpeedListener; //receive swing speed data from ble
  late VoidCallback _bleHitListener; //receive hit data from ble
  bool isSendingGames = false;
  static bool connectionListenerAdded = false; //avoid sending multiple times

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

  ///check internet connection to show winner and how game will be saved
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
  Future<void> cacheGame(int startTime, int gameTypeNum, String winnerName, String loserName, int winnerPoints, int loserPoints, String un, int swingCount, int swingHits, double swingMax, int q1, int q2, int q3, int q4) async {

    Map<String, dynamic> gameToSave = {
      'timestamp': startTime,
      'game_type': gameTypeNum,
      'winner_name': winnerName,
      'loser_name': loserName,
      'winner_points': winnerPoints,
      'loser_points': loserPoints,
      'username': un,
      'swing_count': swingCount,
      'swing_hits': swingHits,
      'swing_max': swingMax,
      'Q1_hits': q1,
      'Q2_hits': q2,
      'Q3_hits': q3,
      'Q4_hits': q4
    };

    final cacheBox = await Hive.openBox("gameQueue");
    await cacheBox.add(gameToSave);

  }

  ///open the Hive box and register each game in the queue to the database
  Future<void> sendCachedGames() async {
    //check for game being sent repeatedly
    if (isSendingGames) {
      print("already sending cached games. skipping duplicate");
      return;
    }

    isSendingGames = true;

    final cacheBox = await Hive.openBox("gameQueue");
    final cacheBoxKeys = cacheBox.keys.toList();
    print("Game queue length: ${cacheBoxKeys.length}");

    for (final key in cacheBoxKeys) {
      try {
        final gameData = await cacheBox.get(key);
        print("Game data at key $key: $gameData");
        if (gameData == null) continue;

        final gameIdMap = await api.registerGame(
          gameData['timestamp'],
          gameData['game_type'],
          gameData['winner_name'],
          gameData['loser_name'],
          gameData['winner_points'],
          gameData['loser_points'],
        );

        final gameID = gameIdMap['game_id'];
        await Future.delayed(Duration(milliseconds: 500)); //try delaying api calls to not overload database on reconnect
        await api.registerStats(
          gameData['username'],
          gameID,
          gameData['swing_count'],
          gameData['swing_hits'],
          gameData['swing_max'],
          gameData['Q1_hits'],
          gameData['Q2_hits'],
          gameData['Q3_hits'],
          gameData['Q4_hits'],
        );

        await cacheBox.delete(key); // delete successfully sent game
      } catch (e) {
        print("Error sending cached game at key $key: $e");
      }
      await Future.delayed(Duration(milliseconds: 500));//try delaying api calls to not overload database on reconnect
    }

    isSendingGames = false;
    await cacheBox.clear();//clear so unsent games don't pile up in box
  }


  ///format game info for saving, cache or register to database, reset game
  void saveAndRestartGame() async{
    int gameTypeNum = game.gameTypeToInt();

    String winnerName = "";
    String loserName = "";

    int winnerPoints = -1;
    int loserPoints = -1;

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
      api.registerStats(un, gameID, game.swingCount, game.swingHits, game.swingMax, game.q1Hits, game.q2Hits, game.q3Hits, game.q4Hits);
      myBLE.writeReset();
      print("Online. Sending game to database $un");
    }
    else{
      //try just turning off wifi instead of full airplane mode
      myBLE.writeReset();
      cacheGame(game.startTime, gameTypeNum, winnerName, loserName, winnerPoints, loserPoints, context.read<User>().username, game.swingCount, game.swingHits, game.swingMax, game.q1Hits, game.q2Hits, game.q3Hits, game.q4Hits);
      print("Offline. Caching game data");
    }


    context.read<User>().setOpponent("");

    setState(() {
      game.resetGame();
    });
  }

  ///reset game from ui
  void _reset(){
    context.read<User>().setOpponent("");
    myBLE.writeReset();
    setState(() {
      game.resetGame();
    });
  }

  ///handle exiting page
  @override
  void dispose() {
    myBLE.latestScoreData.removeListener(_bleDataListener);
    myBLE.latestSwingData.removeListener(_bleSwingSpeedListener);
    myBLE.latestHitData.removeListener(_bleHitListener);
    super.dispose();
  }

  ///when the page is first built, or rebuilt for listener
  @override
  void initState() {
    super.initState();
    loadOpponent(); //get opponent name

    print("init game page");
    ///listen for new button info from paddle
    int prevMyButtonScore = 0;
    int prevOppButtonScore = 0;
    _bleDataListener = () {
      if (!mounted) return;
      final data = myBLE.latestScoreData.value;
      if (data != null) { //new data has been received and a game has been started
        //parse for score data
        int comma1Idx = data.indexOf(',');
        int comma2Idx = data.lastIndexOf(',');
        int length = data.length;
        String myButtonScoreChar = data.substring(0, comma1Idx);
        print("my score char $myButtonScoreChar");
        String oppButtonScoreChar = data.substring(comma1Idx + 1, comma2Idx);
        print("opp score char $oppButtonScoreChar");
        String startButtonPressChar = data.substring(comma2Idx + 1, length);
        int myButtonScore = 0;
        int oppButtonScore = 0;
        int startButtonPress = 0;
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
        try{
          startButtonPress = int.parse(startButtonPressChar);
        }catch(e){
          print("error converting start button press to int $e");
        }

        if(game.inProgress){
          print("Game in progress: ${game.inProgress}");
          if(myButtonScore != prevMyButtonScore){ //my score has changed so increment
            setState(() {
              print("New data in GamePage: $data");
              incMyScore();
              print("My score: ${game.myScore}");
            });
            prevMyButtonScore = myButtonScore;
          }
          if(oppButtonScore != prevOppButtonScore){ //opponent score has changed so increment
            setState(() {
              print("New data in GamePage: $data");
              incOppScore();
              print("Opponent score: ${game.opponentScore}");
            });
            prevOppButtonScore = oppButtonScore;
          }

        }
        else{ //start game with button press
          if(startButtonPress == 1){
            startStandardGame();
          }
        }
      }
    };

    //use the listener function to handle new ble data
    myBLE.latestScoreData.addListener(_bleDataListener);

    ///listen for new swing speed data from paddle
    _bleSwingSpeedListener = () {
      if (!mounted) return; //check widgets
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

    int tempQ1 = 0;
    int tempQ2 = 0;
    int tempQ3 = 0;
    int tempQ4 = 0;

    ///listen for new hit data
    _bleHitListener = () {
      if (!mounted) return;
      final data = myBLE.latestHitData.value;
      if (data != null) { //new data has been received and a game has been started
        if (game.inProgress) {
          print("Hit data: $data");
          //split the comma separated data
          List<String> parts = data.split(',');
          List<int> hits = parts.map(int.parse).toList(); //get the integers and put into list

          print("Hits: $hits");

          setState(() {
            game.newHit(hits[0], hits[1], hits[2], hits[3]);
          });
        } else {
          print("hit will not count until game is started");
        }
      }
    };

    myBLE.latestHitData.addListener(_bleHitListener);
    //when internet connection is restored, immediately send cached games to database
    if (!connectionListenerAdded) {
      internetConnection.connectionRestoreListener(() {
        print("Internet connection restored. Sending cached games");
        sendCachedGames();
      });
      connectionListenerAdded = true;
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
          SizedBox(height: 16),
          Text("Swing Speed ${game.swingMax}"),
          SizedBox(height: 16,),
          Text("Hits - Q1: ${game.q1Hits} Q2: ${game.q2Hits} Q3: ${game.q3Hits} Q4: ${game.q4Hits}"),
          SizedBox(height: 16,),
          ElevatedButton(
              onPressed: _reset,
              child: Text("Reset Game"))
          // Text("Game type: ${game.gameType}"),
          // ElevatedButton(
          //     onPressed: startStandardGame,
          //     child: Text("Start Game")
          // ),
          // ElevatedButton(
          //     onPressed: incMyScore,
          //     child: Text("Inc my score")
          // ),
          // ElevatedButton(
          //     onPressed: incOppScore,
          //     child: Text("Inc opp score")
          // ),
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
    WidgetsBinding.instance.addPostFrameCallback((_) {
      loadUser();
    });
  }

  ///handle friends when online or offline
  Future<void> friendCaching() async {
    final cacheBox = await Hive.openBox("friendQueue");
    //when there's connection, save friends for later
    if (internetConnection.isOnline.value) {
      final friendsToSave = context.read<User>().pals;
      print("Saving friends of type: ${friendsToSave.runtimeType}");
      await cacheBox.put("latestFriends", friendsToSave);
      print("Online: saved pals");
    } else { //when there's not connection load saved friends
      print("Offline: attempting to load cached friends");
      if (cacheBox.containsKey("latestFriends")) {
        final friendData = cacheBox.get("latestFriends");
        print("Loaded cached friends: $friendData");
        context.read<User>().setPals(friendData);
      } else {
        print("No cached friend data available");
      }
    }
  }

  ///refresh user everytime the page is built to keep friends updated
  Future<void> loadUser() async {
    final username = context.read<User>().username;
    if(internetConnection.isOnline.value){
      await context.read<User>().updateUserfromDatabase(username);
    }
    await friendCaching();
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
  List<String> statsToView = ["Wins", "Losses", "Opponents", "Swing Speeds", "Hit Locations"];
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
    List<int> gameIdNums = gameIdDynamic.cast<int>().reversed.toList();

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
        print("WINNER MAP: ${winnerMap}");
        String winnerName = winnerMap[winnerId.toString()];
        //check if the user is the winner
        if (winnerName == username){
          //the user is the winner so save id
          tempWinIds.add(game);
          //get the loser id and username
          int loserID = gameMap[gameIdString]['loser_id'];
          Map<String, dynamic> loserMap = await api.getUsername(loserID);
          String loserName = loserMap[loserID.toString()];
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
        String loserName = loserMap[loserIdString];
        //check if user is the loser
        if (loserName == username){
          //user is the loser so add game to list of loss ids
          tempLossIds.add(game);
          //user winner id to get winner name
          int winnerID = gameMap[gameIdString]['winner_id'];
          Map<String, dynamic> winnerMap = await api.getUsername(winnerID);
          String winnerIdString = winnerID.toString();
          String winnerName = winnerMap[winnerIdString];
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
        String loserName = loserMap[loserIdString];
        //user loses
        if (loserName == username) {
          //use winner id to get opponent name
          int winnerID = gameMap[gameIdString]['winner_id'];
          Map<String, dynamic> winnerMap = await api.getUsername(winnerID);
          String winnerIdString = winnerID.toString();
          String winnerName = winnerMap[winnerIdString];
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

  ///loop through each game to get swing info
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

  ///loop through each game to get hit info
  Future<List<Map<String, dynamic>>> getHitLocations(String username) async {
    List<Map<String, dynamic>> hitsList = [];

    if (gameIds != null){
      List<int> tempIds = gameIds ?? [];
      for (var game in tempIds){
        Map<String, dynamic> gameStatMap = await api.getGameStats(game, username);
        Map<String, dynamic> gameInfoMap = await api.getGameInfo(game);
        String gameIdString = game.toString();
        gameStatMap['date_time'] = DateTime.fromMillisecondsSinceEpoch(gameInfoMap[gameIdString]['timestamp'] * 1000);
        hitsList.add(gameStatMap);
      }
    }

    return hitsList;
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
              title: Text("${swing['date_time']}"),
              subtitle: Text("Max Speed: ${swing[gameIds?[index].toString()]['swing_max']}m/s Swing Count: ${swing[gameIds?[index].toString()]['swing_count']}"),
            );
          }
      ),
    );
  }

  ///display the list of hits
  Widget hitLocationWidget(List<Map<String, dynamic>> hitsList) {
    return Container(
      color: Theme.of(context).cardColor,
      child: ListView.builder(
          itemCount: hitsList.length,
          itemBuilder: (context, index) {
            final hit = hitsList[index];
            return ListTile(
              title: Text("${hit['date_time']} Hit %: ${hit[gameIds?[index].toString()]['hit_percentage']}"),
              subtitle: Text("Q1: ${hit[gameIds?[index].toString()]['Q1_hits']} Q2: ${hit[gameIds?[index].toString()]['Q2_hits']} Q3: ${hit[gameIds?[index].toString()]['Q3_hits']} Q4: ${hit[gameIds?[index].toString()]['Q4_hits']}"),
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
    else if(selectedStat == "Hit Locations"){
      final hits = await getHitLocations(username);
      return hits;
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
                      case "Hit Locations":
                        return hitLocationWidget(data);
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

  final TextEditingController _controller1 = TextEditingController();
  final TextEditingController _controller2 = TextEditingController();

  ///save basic user info for future offline login
  Future<void> cacheUser(String un, String pw) async {
    final userToSave = {
      'username': un.trim(),
      'password': pw.trim(),
    };

    final cacheBox = await Hive.openBox("userQueue");
    await cacheBox.put('cachedUser', userToSave); // use fixed key

    print("User cached");
  }

  ///login offline by checking previously cached user
  Future<void> getCachedUser(String enteredUn, String enteredPw) async {
    final cacheBox = await Hive.openBox("userQueue");

    final userData = cacheBox.get('cachedUser');

    if (userData != null &&
        enteredUn.trim() == userData['username'].trim() &&
        enteredPw.trim() == userData['password'].trim()) {
      print("Offline login approved");
      context.read<User>().setCacheUser(userData['username']);
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      print("Offline login failed");
    }
  }


  ///create new user and log them in
  _createNewUser(String userName, String password) {

    api.postNewUserRequest(userName, password);

    _login(userName, password);
  }

  ///check for valid username and password with database then go to home
  _login(String userName, String password) async {
    //if online login through database
    if(internetConnection.isOnline.value){
      String apiKey = await api.authorizeLogin(userName, password);
      api.apiToken =  apiKey;

      print(apiKey);
      print("LOGIN UN: $userName");

      if(apiKey != ""){
        Provider.of<User>(context, listen: false).updateUserfromDatabase(userName);
        Navigator.pushReplacementNamed(context, '/home');
      }
    }
    else{//if offline login with previously cached user
      print("LOGIN UN: $userName");
      getCachedUser(userName.trim(), password.trim());

    }

  }

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('Login or Create User'),
      ),
      body: Center(
        child: Column(
          children: [
            SizedBox(height: 16,),
            SizedBox(
              width: 350,
              child: TextField(
                controller: _controller1, //username entry is controlled by controller1
                decoration: InputDecoration(
                  labelText: 'Enter username',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            SizedBox(
              height: 16,
            ),
            SizedBox(
              width: 350,
              child: TextField(
                controller: _controller2, //password is controlled by controller2
                decoration: InputDecoration(
                  labelText: 'Enter password',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                ElevatedButton(
                  onPressed: (){
                    _login(_controller1.text, _controller2.text);
                  },
                  child: Text('Login'),

                ),
                SizedBox(width: 16,),
                ElevatedButton(
                    onPressed: (){
                      _createNewUser(_controller1.text, _controller2.text);
                    },
                    child: Text("Create New User")
                )
              ],
            ), //widget holding text entries and button
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
                      if(newValue != null){
                        setState(() {
                          saveChecked = newValue;
                        });

                        if(newValue){
                          cacheUser(_controller1.text, _controller2.text);
                        }
                      }

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
        myBLE.readHitsLiveFromDevice(connectedDevice: device);
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
            Row(
              children: [
                ElevatedButton( //reset user and return to login page on logout
                    onPressed: () {
                      logout();
                      Navigator.pushReplacementNamed(context, '/');
                    },
                    child: Text("Logout")
                ),
                SizedBox(width: 16,),
                // ElevatedButton(
                //     onPressed: myBLE.disconnect,
                //     child: Text("Disconnect device")
                // )
              ],
            ),
            Expanded(
              child: ListView.builder(
                  itemCount: devices.length,
                  itemBuilder: (context, index) {
                    final device = devices[index];
                    return ListTile(
                      tileColor: device.id == myBLE.connectedDevice?.id
                          ? Colors.green[100] // Connected device highlight color
                          : null,
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