import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'dart:async';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';


void main() {
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
  List<String> pals; //may make this a list of users???

  User({
    required this.username,
    required this.gamesPlayed,
    required this.gamesWon,
    required this.avgScore,
    this.pals = const [],  // default to empty list
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

    List<String> friendList = [];

    friendMap.forEach((id, data) {
      final friendUsername = data['username'];
      friendList.add(friendUsername);
    });

    username = userMap['username'];
    gamesPlayed = userMap['gamesPlayed'];
    gamesWon = userMap['gamesWon'];
    avgScore = userMap['averageScore'];
    pals = friendList;

    notifyListeners();
  }

  void notifyNewFriend(String friendUsername){
    pals.add(friendUsername);

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
      case 4:
        page = LoginPage();
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

class GamePage extends StatefulWidget{
  const GamePage({super.key});

  @override
  State<GamePage> createState() => _GamePageState();
}

class _GamePageState extends State<GamePage> {
  var game = Game();
  final serviceUuid = Uuid.parse("91bad492-b950-4226-aa2b-4ede9fa42f59");
  final characteristicUuid = Uuid.parse("ca73b3ba-39f6-4ab3-91ae-186dc9577d99");


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

  void incMyScore(){
    setState(() {
      game.incMyScore();
    });
    print("My Score: ${game.myScore}");
  }

  void incOppScore(){
    setState(() {
      game.incOppScore();
    });
    print("Opp score: ${game.opponentScore}");
  }

  @override
  void initState() {
    super.initState();
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
          Text("Message 1"),
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

  Future<void> showFriends(String username) async{
    try{
      var friends = await api.getFriends(username);
      print("Friends: $friends");
    } catch(e){
      print("error getting friends: $e");
    }
  }

  Future<void> addFriend(String username, String friendUsername) async{
    try{
      var success = await api.addFriend(username, friendUsername);
      print(success["success"]);
      if(success["success"]){
        await context.read<User>().updateUserfromDatabase(username);
      }
      showFriends(username);
    } catch (e){
      print("error adding friend: $e");
    }

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
            // ElevatedButton(
            //     onPressed: () => showFriends(user.username),
            //     child: Text("Show Pals")
            // ),
            Expanded(
              child: ListView.builder(
                  itemCount: user.pals.length,
                  itemBuilder: (context, index) {
                    final pal = user.pals[index];
                    return ListTile(
                      leading: Icon(Icons.person),
                      title: Text(pal),
                      onTap: () => print('Tapped $pal'),
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
  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('History\n(View Stats from Database)'),
      ),
      body: Center(
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
            Container(
              width: 100,
              height: 100,
              color: Colors.blue,
            ),
            SizedBox(height: 16),
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