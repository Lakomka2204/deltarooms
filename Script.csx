using System.Linq;
using UndertaleModLib;
using Newtonsoft.Json;
EnsureDataLoaded();
var roomMap = new Dictionary<int, string>();
for (int i = 0; i < Data.Rooms.Count; i++)
    roomMap[i] = Data.Rooms[i].Name?.Content ?? "";
var globalRoomCode = Data.Code.First(c => c.Name.Content.Contains("scr_get_room_by_id"));
var roomNameCode   = Data.Code.First(c => c.Name.Content.Contains("scr_roomname"));
var result = new Dictionary<string, object>
{
    ["rooms"] = roomMap,
    ["scr_get_room_by_id"] = GetDecompiledText(globalRoomCode),
    ["scr_roomname"] = GetDecompiledText(roomNameCode),
};
Console.Out.WriteLine(JsonConvert.SerializeObject(result, Formatting.Indented));