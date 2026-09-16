# Network Engineer Simulator 3D (จำลองการทำงาน Network Engineer รูปแบบ 3D)

**Network Engineer Simulator 3D** เป็นเกมและโปรแกรมจำลองการทำงานของวิศวกรเครือข่าย (Network Engineer) ในรูปแบบมุมมองบุคคลที่หนึ่ง (3D First-Person) พัฒนาด้วยภาษา **Python**, **Pygame** และ **PyOpenGL**

ผู้เล่นสามารถเดินสำรวจภายในห้อง Data Center / Network Lab จำลอง เข้าใกล้ตู้ Rack 42U ติดตั้ง/ถอดอุปกรณ์ Router, Switch, PC host ตรวจสอบ Port เชื่อมต่อสายเคเบิล Cat6 และเปิดหน้าต่าง Terminal CLI ที่อิงตามคำสั่งของ Cisco IOS เพื่อกำหนดค่าระบบเครือข่ายจริง โดยทุกการกระทำขับเคลื่อนด้วย State และ Logic จริงภายในโปรแกรม ไม่ใช่การจำลองข้อความปลอมบนหน้าจอ

---

## 1. จุดเด่นและระบบสำคัญ (Core Features)

### 3D First-Person Lab Room & Environment
- **ห้องปฏิบัติการขนาด 20m x 15m**: พร้อมพื้นกระเบื้อง Raised Floor, โคมไฟฟลูออเรสเซนต์บนเพดาน, รางเดินสายไฟ Overhead Cable Tray
- **ตู้ Rack มาตรฐาน 42U จำนวน 3 ตู้**: เรียงกันในชื่อ `Rack A`, `Rack B`, และ `Rack C` พร้อมโครงสร้างเสาเหล็ก รางติดตั้งอุปกรณ์ 19 นิ้ว และป้ายชื่อตู้
- **โต๊ะวิศวกร (Engineer Workstation)**: โต๊ะทำงานพร้อมหน้าจอมอนิเตอร์ คีย์บอร์ด เมาส์ และเก้าอี้ สามารถเดินเข้าไปกด `E` เพื่อเปิด Terminal ได้
- **First-Person Controller & AABB Physics**:
  - เดินหน้า/ถอยหลัง/ซ้าย/ขวา (`W`, `A`, `S`, `D`)
  - วิ่ง (`Shift`), กระโดด (`Space`), หันมุมมองด้วยเมาส์
  - ระบบตรวจสอบการชน (AABB Collision) ไม่สามารถเดินทะลุกำแพง โต๊ะ หรือตู้ Rack ได้ พร้อมระบบ Axial Sliding เดินเลียบกำแพงได้อย่างนุ่มนวล

### ระบบ Rack & Device Occupancy (42U Real State)
- **รองรับหน่วยความสูง 1U - 42U**: ตรวจสอบขอบเขตความสูงอย่างแม่นยำ
- **ระบบป้องกันการติดตั้งซ้อนทับ (Collision Prevention)**: หากช่อง U นั้นมีอุปกรณ์ติดตั้งอยู่แล้ว ระบบจะปฏิเสธการติดตั้งซ้ำทันที
- **อุปกรณ์ 3 ประเภทหลัก**:
  1. **Router (2U)**: มีพอร์ต GigabitEthernet (`Gi0/0`, `Gi0/1`), พอร์ต `Console`, Routing Table, Cisco Router CLI
  2. **Switch (1U)**: มีพอร์ต GigabitEthernet 24 พอร์ต (`Gi0/1` ถึง `Gi0/24`), MAC Address Table พร้อมระบบ Dynamic Learning, VLAN
  3. **PC Workstation (2U)**: มีพอร์ต Ethernet `eth0`, การตั้งค่า IP, Subnet Mask, Default Gateway, และ Windows CMD Prompt

### ระบบ Port & Decoupled State
- **การแยกสถานะทางกายภาพและสถานะการจัดการอย่างเด็ดขาด**:
  - `ADMIN UP` / `ADMIN DOWN` (กำหนดผ่าน CLI เช่น `shutdown` / `no shutdown`)
  - `LINK UP` / `LINK DOWN` (ขึ้นอยู่กับการมีสายเชื่อมต่อและพอร์ตปลายทางเปิดใช้งาน)
- **ไฟสถานะ LED บนหน้าปัด 3D**: ไฟสีเขียวเมื่อพอร์ต Operational (Admin UP + Link UP) และดับเมื่อ Link DOWN

### ระบบสายสัญญาณ (Physical Cable System)
- **สายเคเบิล Cat6 Ethernet**: เชื่อมต่อระหว่าง Port A และ Port B
- **ตรวจสอบความถูกต้อง**: ป้องกันการเสียบพอร์ตเดิมซ้ำ (Occupied Port) และป้องกันการต่อสายวนกลับพอร์ตตัวเอง (Self-loop)
- **การเรนเดอร์สายเคเบิล 3D**: แสดงเส้นโค้งห้อยย้อยตามธรรมชาติ (Catenary Sag) เชื่อมระหว่างพอร์ตบนตู้ Rack

### ระบบ Cisco IOS-Inspired CLI & PC Terminal
- **CLI Modal Context รองรับระดับ Mode จริง**:
  - `User EXEC`: `Router>` / `Switch>`
  - `Privileged EXEC`: `Router#` / `Switch#` (คำสั่ง `enable`, `disable`)
  - `Global Configuration`: `Router(config)#` (คำสั่ง `configure terminal`)
  - `Interface Configuration`: `Router(config-if)#` (คำสั่ง `interface gi0/0`)
- **คำสั่งที่มีผลต่อ State ของอุปกรณ์จริง**:
  - `hostname <name>`: เปลี่ยนชื่อโฮสต์ของอุปกรณ์ทันที
  - `interface <name>`: สลับเข้าสู่ Context ของ Interface นั้น
  - `ip address <ip> <subnet_mask>`: กำหนด IP ให้ Interface จริง
  - `shutdown` / `no shutdown`: ปิด/เปิดพอร์ต และอัปเดตสถานะเครือข่ายทันที
  - `ip route <dest> <mask> <next-hop>`: เพิ่ม Static Route ใน Routing Table
  - `show running-config`: สร้าง Config ปัจจุบันจาก State จริงของเครื่อง
  - `show ip interface brief`: แสดงตารางสรุปสถานะพอร์ตและ IP
  - `show mac address-table`: แสดงตาราง MAC ที่ Switch เรียนรู้ได้จริง
  - `show ip route`: แสดง Routing Table
  - `ping <destination_ip>`: ยิงคำสั่ง ICMP Ping ผ่าน NetworkEngine จริง
- **PC Command Prompt**:
  - `ipconfig` / `ipconfig /all`: ตรวจสอบสถานะการเชื่อมต่อ
  - `ipconfig /set <ip> <subnet_mask> [gateway]`: ตั้งค่า IP และ Gateway
  - `ping <destination_ip>`: ทดสอบการเชื่อมต่อไปยังโฮสต์ปลายทาง
  - `arp -a`: ดูตาราง ARP Cache
- **คุณสมบัติของหน้าต่าง Terminal UI**:
  - พื้นหลังสีเข้ม (Dark Theme) ตัดกับ UI หลัก
  - รองรับ Command History ผ่านปุ่มลูกศร `UP` / `DOWN`
  - รองรับ Auto-complete คำสั่งผ่านปุ่ม `TAB`
  - รองรับการยกเลิกคำสั่งผ่าน `Ctrl + C`
  - เคอร์เซอร์กะพริบและ Scrollback buffer

### Network Engine (Logical Simulation)
- การคำนวณ Subnetting (CIDR, Netmask, Network Address, Broadcast)
- การสวิตชิ่ง Layer 2: ตรวจสอบเส้นทาง Physical Cable และ Switch Flooding / MAC Forwarding
- การส่งต่อ Layer 3: ตรวจสอบ Subnet เดียวกัน หรือส่งต่อผ่าน Default Gateway และคำนวณเส้นทางผ่าน Router
- การทดสอบ Ping (ICMP Echo):
  - แจ้งข้อผิดพลาดชัดเจนหาก Interface ถูก Shutdown, สายเคเบิลหลุด, หรือไม่มี Gateway

### Modern Light Theme UI
- หน้า **Main Menu** ธีมสว่าง สะอาด ทันสมัย: การ์ดโค้งมน (Rounded Corners), แสงเงา Elevation, สี Accent Highlight (Royal Blue)
- หน้า **HUD**: แถบสถานะด้านบนระบุโหมด, อุปกรณ์ที่มองอยู่, Network Status และ FPS, เป้าเล็งกากบาทตรงกลาง, และคำแนะนำปุ่มกดด้านล่าง
- **Modal Panel**: หน้าต่างจัดการอุปกรณ์ในตู้ Rack และหน้าต่าง Inventory (`TAB`)

---

## 2. โครงสร้างโฟลเดอร์ของโปรเจกต์ (Project Structure)

โปรเจกต์ถูกออกแบบตามหลัก OOP และ Separation of Concerns โดยแยกการทำงานแต่ละส่วนออกจากกันอย่างชัดเจน:

```text
network_sim/
├── main.py                     # Entry point & Runtime Bootstrap
├── run.bat                     # สคริปต์รันโปรแกรมสำหรับ Windows
├── requirements.txt            # รายการ Dependencies
├── README.md                   # คู่มือภาษาไทย
│
├── config/                     # การตั้งค่าค่าคงที่ของระบบ
│   ├── game_config.py          # ความละเอียดหน้าจอ, ความเร็วผู้เล่น, มิติตู้ Rack
│   ├── graphics_config.py      # สีของ UI Light Theme / Terminal และ 3D Materials
│   └── network_config.py       # ค่าเริ่มต้นเครือข่ายและ Subnet
│
├── core/                       # แกนหลักของ Game Engine
│   ├── game.py                 # Loop หลัก, Pygame Window & Context
│   ├── game_state.py           # GameState Machine (MAIN_MENU, SANDBOX, etc.)
│   ├── event_bus.py            # ระบบ Publish/Subscribe Event Bus
│   ├── input_manager.py        # จัดการอินพุตเมาส์และคีย์บอร์ด
│   ├── time_manager.py         # คำนวณ Delta Time และจำกัด Framerate
│   └── service_container.py    # Service Locator / Dependency Injection
│
├── rendering/                  # ระบบแสดงผล 3D & 2D OpenGL
│   ├── renderer.py             # Viewport, 3D Perspective & 2D Ortho passes
│   ├── camera.py               # First-Person Camera (Yaw, Pitch, Forward Vector)
│   ├── lighting.py             # แสงไฟฟลูออเรสเซนต์ในห้อง Data Center
│   ├── primitives.py           # การวาด Box, Cylinder, Grid, 3D Line
│   └── ui_renderer.py          # การวาดการ์ด 2D, ตัวอักษร Font Cache คมชัด
│
├── world/                      # โลก 3D และวัตถุในห้อง
│   ├── world.py                # ตัวจัดการ Room, Racks, Desk, Devices
│   ├── room.py                 # ห้อง 20m x 15m, พื้น Grid, ผนัง, รางสายไฟ
│   ├── rack.py                 # ตู้ Rack 42U พร้อมระบบตรวจจับ Occupancy
│   ├── desk.py                 # โต๊ะ Engineer Workstation พร้อมจอ Monitor
│   └── interactable.py         # คลาสแม่สำหรับวัตถุที่สามารถมองและกด E ได้
│
├── player/                     # ผู้เล่นและระบบฟิสิกส์
│   ├── player.py               # ตัวละครผู้เล่น
│   ├── controller.py           # การควบคุม WASD, วิ่ง, กระโดด, หันเมาส์
│   ├── collision.py            # การตรวจจับการชน AABB และ Axial Sliding
│   └── interaction.py          # Raycast ตรวจจับวัตถุเป้าหมายในระยะมือถึง
│
├── devices/                    # อุปกรณ์ฮาร์ดแวร์เครือข่าย
│   ├── device.py               # คลาสแม่ Device
│   ├── router.py               # อุปกรณ์ Router 2U
│   ├── switch.py               # อุปกรณ์ Switch 1U (24 พอร์ต)
│   ├── pc.py                   # อุปกรณ์ PC Host 2U
│   ├── port.py                 # พอร์ตเชื่อมต่อ (Admin/Link Decoupled Status)
│   ├── device_factory.py       # Factory สำหรับสร้างอุปกรณ์พร้อม ID อัตโนมัติ
│   └── models/                 # โมเดล 3D ที่แยกขาดจาก Logic
│       ├── router_model.py     # โมเดล 3D Router (Faceplate, LEDs, Gigabit Ports)
│       ├── switch_model.py     # โมเดล 3D Switch (24 RJ45 Ports, LEDs)
│       └── pc_model.py         # โมเดล 3D PC Case & I/O
│
├── network/                    # เครื่องยนต์จำลองเน็ตเวิร์กเชิงตรรกะ
│   ├── network_engine.py       # การสวิตชิ่ง L2, การเราต์ L3, ICMP Ping
│   ├── subnet.py               # การคำนวณและแปลงค่า Subnet IPv4
│   ├── packet.py               # โครงสร้างข้อมูล Packet / Frame
│   └── routing_table.py        # ตารางเราต์พร้อม Longest Prefix Match
│
├── cables/                     # ระบบสายสัญญาณ
│   ├── cable.py                # อ็อบเจกต์สาย Cat6
│   ├── cable_manager.py        # การเสียบสาย, ถอดสาย, ตรวจสอบความถูกต้อง
│   └── cable_renderer.py       # เรนเดอร์สายเคเบิล 3D พร้อมความโค้งหย่อน
│
├── cli/                        # ระบบ CLI Console
│   ├── cli_engine.py           # ควบคุม Session, ประวัติคำสั่ง, Tab Autocomplete
│   ├── cli_context.py          # จัดการ Cisco Prompt Level (EXEC, Config, Config-if)
│   ├── cli_parser.py           # ตัวตัดคำและแจกแจง Arguments
│   ├── router_cli.py           # ชุดคำสั่ง Cisco Router
│   ├── switch_cli.py           # ชุดคำสั่ง Cisco Switch
│   └── pc_cli.py               # ชุดคำสั่ง Windows CMD บน PC
│
├── inventory/                  # ระบบคลังอุปกรณ์ของผู้เล่น
│   ├── inventory.py            # ติดตามจำนวนอุปกรณ์และสายสัญญาณ
│   └── item.py                 # ชนิดไอเทม (Router, Switch, PC, Cable)
│
├── ui/                         # ส่วนต่อประสานผู้ใช้ (Modern UI)
│   ├── main_menu.py            # เมนูหลักสไตล์ Modern Light Theme
│   ├── hud.py                  # HUD ในเกม, เป้าเล็ง, ข้อความบอกใบ้
│   ├── terminal.py             # หน้าต่าง Terminal Overlay สีเข้ม
│   ├── interaction_panel.py    # Modal ติดตั้ง/ถอดอุปกรณ์, สลับเข้า CLI
│   ├── inventory_ui.py         # หน้าต่างแสดงคลังอุปกรณ์ (TAB)
│   ├── debug_overlay.py        # หน้าต่างข้อมูล Debug ของผู้พัฒนา (F3)
│   └── widgets/                # วิดเจ็ต Button, Panel, Label
│
├── save/                       # ระบบบันทึกและโหลดสถานะเกม
│   ├── save_serializer.py      # แปลงสถานะ World, Racks, Cables เป็น JSON
│   └── save_manager.py         # อ่าน/เขียนไฟล์ JSON
│
└── tests/                      # ชุดทดสอบ Unit Test ครอบคลุมทุกโมดูล
    ├── test_ports.py           # ทดสอบสถานะ Admin/Link และการตัดการเชื่อมต่อ
    ├── test_cables.py          # ทดสอบการต่อสาย, ป้องกัน Self-loop และพอร์ตซ้อน
    ├── test_rack.py            # ทดสอบตู้ 42U, การติดตั้ง, และตรวจการซ้อนทับ
    ├── test_cli.py             # ทดสอบ Cisco Modes, คำสั่ง และการเปลี่ยน State
    ├── test_network_engine.py  # ทดสอบ Subnetting, MAC Table, Routing, Ping
    └── test_save_load.py       # ทดสอบการบันทึกและโหลดข้อมูล JSON
```

---

## 3. ความต้องการของระบบ (System Requirements & Dependencies)

- **ระบบปฏิบัติการ**: Windows 10 / 11, Linux, หรือ macOS
- **ภาษา**: Python 3.10 หรือ Python 3.11 ขึ้นไป
- **Libraries หลัก**:
  - `pygame >= 2.5.0`
  - `PyOpenGL >= 3.1.6`
  - `PyOpenGL-accelerate >= 3.1.6`
  - `numpy >= 1.24.0`
  - `pytest >= 8.0.0` (สำหรับรัน Unit Test)

---

## 4. วิธีการติดตั้งและการเข้าเล่นเกม (Installation & How to Run)

### ติดตั้ง Dependencies
```powershell
pip install -r requirements.txt
```

### การเปิดเกม
สามารถเปิดเล่นเกมได้ทันทีผ่านคำสั่ง:
```powershell
python main.py
```
หรือหากเครื่องมีตัวเรียกใช้ Python 3.11 (Python Launcher):
```powershell
py -3.11 main.py
```
หรือบน Windows สามารถดับเบิลคลิกไฟล์ **`run.bat`** เพื่อเปิดเกมได้โดยตรง

---

## 5. การควบคุมภายในเกม (Controls)

| ปุ่ม | หน้าที่ |
| :--- | :--- |
| **W, A, S, D** | เดินหน้า, ซ้าย, ถอยหลัง, ขวา |
| **Mouse Movement** | หันมุมมองกล้อง 3D (First-Person Look) |
| **Left Shift** | วิ่ง (Sprint) |
| **Spacebar** | กระโดด (Jump) |
| **E** | โต้ตอบ (Interact) กับตู้ Rack, อุปกรณ์ หรือโต๊ะ Engineer |
| **TAB** | เปิด/ปิด หน้าต่างคลังอุปกรณ์ (Inventory) |
| **F3** | เปิด/ปิด หน้าต่างข้อมูล Debug (FPS, พิกัด, ลิงก์ที่ทำงาน) |
| **ESC** | ปิดหน้าต่าง Modal / ออกไปยังเมนูหลัก |
| **Mouse Left Click** | คลิกปุ่มบนหน้าต่าง UI |

---

## 6. การทดสอบอัตโนมัติ (Automated Unit Tests)

โปรเจกต์มาพร้อมกับชุดทดสอบ Unit Test 23 รายการ ซึ่งทำงานโดยแยกขาดจากกราฟิก (Decoupled from OpenGL):

รันชุดทดสอบทั้งหมดด้วยคำสั่ง:
```powershell
py -3.11 -m pytest tests/ -v
```

ผลการทดสอบ:
```text
tests/test_cables.py::test_cable_direct_connection PASSED
tests/test_cables.py::test_cable_prevent_self_loop PASSED
tests/test_cables.py::test_cable_prevent_occupied_port PASSED
tests/test_cables.py::test_cable_manager_removal PASSED
tests/test_cli.py::test_router_cli_mode_transitions PASSED
tests/test_cli.py::test_router_cli_state_mutations PASSED
tests/test_cli.py::test_switch_cli_vlan_mutation PASSED
tests/test_cli.py::test_pc_cli_ipconfig_set PASSED
tests/test_network_engine.py::test_subnet_math PASSED
tests/test_network_engine.py::test_network_engine_end_to_end_ping_success PASSED
tests/test_network_engine.py::test_network_engine_ping_failure_on_cable_disconnect PASSED
tests/test_network_engine.py::test_network_engine_ping_failure_on_interface_shutdown PASSED
tests/test_ports.py::test_port_initial_states PASSED
tests/test_ports.py::test_port_admin_up_no_cable PASSED
tests/test_ports.py::test_port_cable_connection_both_up PASSED
tests/test_ports.py::test_port_one_side_admin_down PASSED
tests/test_ports.py::test_port_disconnect PASSED
tests/test_rack.py::test_rack_dimensions_and_capacity PASSED
tests/test_rack.py::test_install_devices_in_rack PASSED
tests/test_rack.py::test_rack_occupancy_collision_prevention PASSED
tests/test_rack.py::test_rack_boundary_checks PASSED
tests/test_rack.py::test_rack_device_removal PASSED
tests/test_save_load.py::test_save_serialization_and_disk_io PASSED
============================= 23 passed in 0.43s ==============================
```

---

## 7. แผนการพัฒนาในอนาคต (Future Roadmap)

- **Phase 2 - Tutorial & Guided Scenarios**: ดำเนินการสร้างฉากสอนทีละขั้นตอน (เสียบสาย ตั้งค่า IP เราต์ และทดสอบ Ping)
- **Phase 3 - Dynamic Protocols**: จำลองโปรโตคอลเครือข่ายเพิ่มเติม เช่น DHCP Server/Client, DNS Resolver, NAT (Network Address Translation), และ Static ACLs
- **Phase 4 - Packet Inspection**: ระบบจำลองการดักจับแพ็กเก็ต (Packet Sniffer / Wireshark-like viewer) เพื่อดูข้อมูล Header และ Payload แบบเรียลไทม์
- **Phase 5 - Routing Protocols**: การจำลอง OSPFv2 (Link-State Advertisements, Dijkstra Shortest Path) และ BGP พื้นฐาน
