from enum import Enum
import struct
import sys
import os

from fastapi import FastAPI
from pydantic import BaseModel

## backend -> frontend
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

class RegisterInput(BaseModel):
    registerString: str

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"
    
class ConfigFileParser(object):
    def __init__(self, filename):
        self.filename : str = filename
        
        # La cabecera inicial de 6 bytes
        self.HEADER_SIZE = 6

        # Estructura tsICfgGenParam (18 bytes según los tipos de datos)
        self.TS_ICFG_GEN_PARAM_FORMAT = "4B8H"
        self.TS_ICFG_GEN_PARAM_SIZE = struct.calcsize(self.TS_ICFG_GEN_PARAM_FORMAT)
        
        self.tsICfgTicket_format = (
        "< H B 32s 32s 32s 32s B B 64s "  
        "B B B I B H B B B B B B B B "  
        "B B B B B B B B B B B B B B B B B B B B B B B B B B B B "  
        "2I 8s 8s H H "  
        "I I I I I "  
        "10I "  
        "10I "  
        "I I"  
    )

        # Estructura tsICfgOriginDestination (3 bytes: 1 byte Origen, 1 byte Destino, 1 byte Descuento)
        self.TS_ICFG_ORIGIN_DEST_FORMAT = "3B"
        self.TS_ICFG_TRANSFERS = "8B"
        self.TS_ICFG_TRANSFERS_SIZE = struct.calcsize(self.TS_ICFG_TRANSFERS)
        self.TS_ICFG_ORIGIN_DEST_SIZE = struct.calcsize(self.TS_ICFG_ORIGIN_DEST_FORMAT)

    def read_binary_file(self):
        with open(self.filename, "rb") as f:
            data = f.read()
        
        return data

    def parse_param_file(self, buffer):
        output = []
        offset = 0
        
        version = struct.unpack_from("<H", buffer, offset)[0]
        output.append(f"Version: {version}\n")

        # Saltar la cabecera de 6 bytes
        offset += self.HEADER_SIZE

        # Extraer tsICfgGenParam
        gen_param = struct.unpack_from(self.TS_ICFG_GEN_PARAM_FORMAT, buffer, offset)
        offset += self.TS_ICFG_GEN_PARAM_SIZE

        output.append("===== tsICfgGenParam =====\n")
        output.append(f"bCSCUpperVersion: {gen_param[0]}\n")
        output.append(f"bCSCLowerVersion: {gen_param[1]}\n")
        output.append(f"bCPSCUpperVersion: {gen_param[2]}\n")
        output.append(f"bCPSCLowerVersion: {gen_param[3]}\n")
        output.append(f"wPassbackTime: {gen_param[4]}\n")
        output.append(f"wMinDiscount: {gen_param[5]}\n")
        output.append(f"wMiddleMinDiscount: {gen_param[6]}\n")
        output.append(f"wMiddleMaxDiscount: {gen_param[7]}\n")
        output.append(f"wMaxDiscount: {gen_param[8]}\n")
        output.append(f"wQRMaxValidityTime: {gen_param[9]}\n")
        output.append(f"wQRMaxValidationTime: {gen_param[10]}\n")
        output.append(f"wNumofActiveStations: {gen_param[11]}\n")
        output.append("=========================\n")
        
        # Leer los registros de tsICfgOriginDestination hasta el final del buffer
        output.append("\n===== tsICfgOriginDestination Records =====\n")
        
        zones = []
        while offset + self.TS_ICFG_ORIGIN_DEST_SIZE <= len(buffer):
            origin_dest = struct.unpack_from(self.TS_ICFG_ORIGIN_DEST_FORMAT, buffer, offset)
            offset += self.TS_ICFG_ORIGIN_DEST_SIZE
            output.append(f"Origen: {origin_dest[0]}, Destino: {origin_dest[1]}, Descuento: {origin_dest[2]}\n")
            zones.append(origin_dest)

        output.append("===========================================\n")
        
        return gen_param, zones
    
    
    def parse_titulos_file(self, data):
        output = []
        
        tsICfgTicket_size = struct.calcsize(self.tsICfgTicket_format)

        version_bytes = data[:2]
        version = struct.unpack("<H", version_bytes)[0]
        output.append(f"Tamaño esperado de tsICfgTicket: {tsICfgTicket_size} bytes")
        output.append(f"Version: {version}\n")

        offset = self.HEADER_SIZE

        while offset < len(data):
            chunk = data[offset:offset + tsICfgTicket_size]

            if len(chunk) < tsICfgTicket_size:
                output.append(f"Error: chunk leído ({len(chunk)} bytes) es menor que el tamaño esperado ({tsICfgTicket_size} bytes).")
                break

            ticket = struct.unpack(self.tsICfgTicket_format, chunk)
            baSpanishName = ticket[2].decode('latin1').strip('\x00')
            baEnglishName = ticket[3].decode('latin1').strip('\x00')
            baFrenchName = ticket[4].decode('latin1').strip('\x00')
            baGermanName = ticket[5].decode('latin1').strip('\x00')
            
            """baaTransferTimes = [list(ticket[8][i * 8:(i + 1) * 8]) for i in range(8)]
            baNoEntryTransferTimes = list(ticket[56:64])
            baTransferPenaltyTimes = list(ticket[64:72])
            raw_discounts = ticket[72:82]  # 10 DWORDs
            raw_midle_discounts = ticket[82:92]  # 10 DWORDs """

            baaTransferTimes = []
            offset2 = offset + 8
            for i in range(8):
                unpacked_data  = struct.unpack_from(self.TS_ICFG_TRANSFERS, data, offset2)
                offset2 += self.TS_ICFG_TRANSFERS_SIZE
                baaTransferTimes.append( unpacked_data )

            baNoEntryTransferTimes = list(ticket[53])
            baTransferPenaltyTimes = list(ticket[54])
            raw_discounts = ticket[62:72]  # 10 DWORDs
            raw_midle_discounts = ticket[72:82]  # 10 DWORDs

            tsaDiscount = [(raw_discounts[i], raw_discounts[i + 1]) for i in range(0, len(raw_discounts), 2)]
            tsaMidleDiscount = [(raw_midle_discounts[i], raw_midle_discounts[i + 1]) for i in range(0, len(raw_midle_discounts), 2)]
            
            output.append(f"Ticket Code: {ticket[0]}\n")
            output.append(f"Fare Type: {ticket[1]}\n")
            output.append(f"Spanish Name: {baSpanishName}\n")
            output.append(f"English Name: {baEnglishName}\n")
            output.append(f"French Name: {baFrenchName}\n")
            output.append(f"German Name: {baGermanName}\n")
            output.append(f"Representation Type: {ticket[6]}\n")
            output.append(f"Area Control: {ticket[7]}\n")
            output.append(f"Day Validity: {ticket[9]}\n")
            output.append(f"Week Validity: {ticket[10]}\n")
            output.append(f"Proprietary Company: {ticket[11]}\n")
            output.append(f"Valid Operators: {ticket[12]}\n")
            output.append(f"Balance Type: {ticket[13]}\n")
            output.append(f"Number of Trips: {ticket[14]}\n")
            output.append(f"Balance Period Value: {ticket[15]}\n")
            output.append(f"Balance Period Units: {ticket[16]}\n")
            output.append(f"Time Validity Exp Type At Sale: {ticket[17]}\n")
            output.append(f"Time Validity Begin Type At Val: {ticket[18]}\n")
            output.append(f"Time Validity Exp Type At Val: {ticket[19]}\n")
            output.append(f"Time Validity Begin At Val Ctrl: {ticket[20]}\n")
            output.append(f"Time Validity Exp At Val Ctrl: {ticket[21]}\n")
            output.append(f"No Entry Transfer Times: {baNoEntryTransferTimes}\n")
            output.append(f"Transfer Penalty Times: {baTransferPenaltyTimes}\n")
            output.append(f"Discounts: {tsaDiscount}\n")
            output.append(f"Middle Discounts: {tsaMidleDiscount}\n")
            output.append(f"Max Entry to Exit Time: {ticket[32]}\n")
            output.append("-" * 50)

            offset += tsICfgTicket_size

        return output, baaTransferTimes

    def parse_titulos_file2(self, data):
        titulos = []
        
        tsICfgTicket_size = struct.calcsize(self.tsICfgTicket_format)

        version_bytes = data[:2]
        version = struct.unpack("<H", version_bytes)[0]

        offset = self.HEADER_SIZE

        while offset < len(data):
            output = []
            output.append(f"Tamaño esperado de tsICfgTicket: {tsICfgTicket_size} bytes")
            output.append(f"Version: {version}\n")
            chunk = data[offset:offset + tsICfgTicket_size]

            if len(chunk) < tsICfgTicket_size:
                output.append(f"Error: chunk leído ({len(chunk)} bytes) es menor que el tamaño esperado ({tsICfgTicket_size} bytes).")
                break

            ticket = struct.unpack(self.tsICfgTicket_format, chunk)
            baSpanishName = ticket[2].decode('latin1').strip('\x00')
            baEnglishName = ticket[3].decode('latin1').strip('\x00')
            baFrenchName = ticket[4].decode('latin1').strip('\x00')
            baGermanName = ticket[5].decode('latin1').strip('\x00')
            
            """baaTransferTimes = [list(ticket[8][i * 8:(i + 1) * 8]) for i in range(8)]
            baNoEntryTransferTimes = list(ticket[56:64])
            baTransferPenaltyTimes = list(ticket[64:72])
            raw_discounts = ticket[72:82]  # 10 DWORDs
            raw_midle_discounts = ticket[82:92]  # 10 DWORDs """

            baaTransferTimes = []
            offset2 = offset + 8
            for i in range(8):
                unpacked_data  = struct.unpack_from(self.TS_ICFG_TRANSFERS, data, offset2)
                offset2 += self.TS_ICFG_TRANSFERS_SIZE
                baaTransferTimes.append( unpacked_data )

            baNoEntryTransferTimes = list(ticket[53])
            baTransferPenaltyTimes = list(ticket[54])
            raw_discounts = ticket[62:72]  # 10 DWORDs
            raw_midle_discounts = ticket[72:82]  # 10 DWORDs

            tsaDiscount = [(raw_discounts[i], raw_discounts[i + 1]) for i in range(0, len(raw_discounts), 2)]
            tsaMidleDiscount = [(raw_midle_discounts[i], raw_midle_discounts[i + 1]) for i in range(0, len(raw_midle_discounts), 2)]
            
            output.append(f"Ticket Code: {ticket[0]}\n")
            output.append(f"Fare Type: {ticket[1]}\n")
            output.append(f"Spanish Name: {baSpanishName}\n")
            output.append(f"English Name: {baEnglishName}\n")
            output.append(f"French Name: {baFrenchName}\n")
            output.append(f"German Name: {baGermanName}\n")
            output.append(f"Representation Type: {ticket[6]}\n")
            output.append(f"Area Control: {ticket[7]}\n")
            output.append(f"Day Validity: {ticket[9]}\n")
            output.append(f"Week Validity: {ticket[10]}\n")
            output.append(f"Proprietary Company: {ticket[11]}\n")
            output.append(f"Valid Operators: {ticket[12]}\n")
            output.append(f"Balance Type: {ticket[13]}\n")
            output.append(f"Number of Trips: {ticket[14]}\n")
            output.append(f"Balance Period Value: {ticket[15]}\n")
            output.append(f"Balance Period Units: {ticket[16]}\n")
            output.append(f"Time Validity Exp Type At Sale: {ticket[17]}\n")
            output.append(f"Time Validity Begin Type At Val: {ticket[18]}\n")
            output.append(f"Time Validity Exp Type At Val: {ticket[19]}\n")
            output.append(f"Time Validity Begin At Val Ctrl: {ticket[20]}\n")
            output.append(f"Time Validity Exp At Val Ctrl: {ticket[21]}\n")
            output.append(f"No Entry Transfer Times: {baNoEntryTransferTimes}\n")
            output.append(f"Transfer Penalty Times: {baTransferPenaltyTimes}\n")
            output.append(f"Discounts: {tsaDiscount}\n")
            output.append(f"Middle Discounts: {tsaMidleDiscount}\n")
            output.append(f"Max Entry to Exit Time: {ticket[32]}\n")
            output.append("-" * 50)

            offset += tsICfgTicket_size
            
            titulos.append(output)

        return titulos, baaTransferTimes
    
    
class RegisterParser(object):
    def __init__(self, register_string):
        self.register_string = register_string
        
    
    def hexstr_to_bytes(self) -> bytes:
        # Elimina prefijos tipo "0x" y convierte a bytes
        self.register_string = self.register_string.lower().replace("0x", "").replace(" ", "")
        return bytes.fromhex(self.register_string)

    def read_bits(self, data: bytes, bit_offset: int, num_bits: int) -> int:
        byte_offset = bit_offset // 8
        bit_index = bit_offset % 8
        total_bits = bit_index + num_bits
        num_bytes = (total_bits + 7) // 8
        relevant_bytes = data[byte_offset:byte_offset + num_bytes]
        value = int.from_bytes(relevant_bytes, byteorder='little')
        value >>= bit_index
        mask = (1 << num_bits) - 1
        return value & mask

    def parse(self, data : bytes):

        print(f"Cadena binaria: {data}")

        # Definición de las variables con las posiciones en bits y tamaños en bits
        result = {}
        
        result['RecordVersion'] = data[0]  # 8 bits
        result['wType'] = int.from_bytes(data[1:3], 'little')
        # Obtenemos el número de serie del dispositivo (4 bytes = 32 bits
        result['DeviceSerialNumber'] = int.from_bytes(data[3:7], 'little')
        result['TransactionSequence'] = int.from_bytes(data[7:11], 'little')
        # Obtenemos el UID de la tarjeta (7 bytes = 56 bits)    
        
        result['SerialNumber'] = self.read_bits(data, 88, 56)
        #Cabecera 11 bytes. Le quitamos la cabecera a data
        #data = data[144:]  # 11 bytes + 7 bytes CTL uid
        offset = 88

        # Asignamos los datos a las variables indicadas (usando posiciones y tamaños en bits)
        #result['l_bpAux'] = data
        #result['l_bUidAux'] = self.read_bits(data, 0, 56)  # 56 bits
        result['bType'] = self.read_bits(data, offset + 56, 4)  # 4 bits
        result['bSubType'] = self.read_bits(data, offset + 60, 4)  # 4 bits
        result['bVersion'] = self.read_bits(data, offset + 64, 4)  # 4 bits
        result['bCompany'] = self.read_bits(data, offset + 68, 5)  # 5 bits
        result['bEndOfValidityDay'] = self.read_bits(data, offset + 73, 5)  # 5 bits
        result['bEndOfValidityMonth'] = self.read_bits(data, offset + 78, 4)  # 4 bits
        result['bEndOfValidityYear'] = self.read_bits(data, offset + 82, 5)  # 5 bits
        result['bCardEnabled'] = self.read_bits(data, offset + 87, 1)  # 1 bit
        result['bTransactionNumber'] = self.read_bits(data, offset + 88, 4)  # 4 bits
        result['bEnabledTickets'] = self.read_bits(data, offset + 104, 4)  # 4 bits
        result['bLastTicketUsed'] = self.read_bits(data, offset + 108, 2)  # 2 bits
        result['bCompany_2'] = self.read_bits(data, offset + 120, 5)  # 5 bits
        result['wCode'] = self.read_bits(data, offset + 125, 12)  # 12 bits
        result['bDayValidity'] = self.read_bits(data, offset + 137, 4)  # 4 bits
        result['bWeekValidity'] = self.read_bits(data, offset + 141, 4)  # 4 bits
        result['bFareType'] = self.read_bits(data, offset + 145, 4)  # 4 bits
        result['bFareIndex'] = self.read_bits(data, offset + 149, 3)  # 3 bits
        result['bZoneValidity'] = self.read_bits(data, offset + 152, 8)  # 8 bits
        result['bTypeOfTimeValidityUnits'] = self.read_bits(data, offset + 160, 3)  # 3 bits
        result['bNoOfTimeValidityUnits'] = self.read_bits(data, offset + 163, 8)  # 8 bits
        result['bUseTripsBalance'] = self.read_bits(data, offset + 171, 1)  # 1 bit
        result['bPrevTicketIsExtended'] = self.read_bits(data, offset + 184, 1)  # 1 bit
        result['bPrevTimeValidityDay'] = self.read_bits(data, offset + 185, 5)  # 5 bits
        result['bPrevTimeValidityMonth'] = self.read_bits(data, offset + 190, 4)  # 4 bits
        result['bPrevTimeValidityYear'] = self.read_bits(data, offset + 194, 5)  # 5 bits
        result['bPrevTimeValidityHour'] = self.read_bits(data, offset + 199, 5)  # 5 bits
        result['bPrevTimeValidityMinute'] = self.read_bits(data, offset + 204, 6)  # 6 bits
        result['bPrevTripBalance'] = self.read_bits(data, offset + 210, 8)  # 8 bits
        result['bPrevDayTripCounter'] = self.read_bits(data, offset + 218, 3)  # 3 bits
        result['bPrevLastValidationDay'] = self.read_bits(data, offset + 221, 5)  # 5 bits
        result['bTicketIsExtended'] = self.read_bits(data, offset + 240, 1)  # 1 bit
        result['bTimeValidityDay'] = self.read_bits(data, offset + 241, 5)  # 5 bits
        result['bTimeValidityMonth'] = self.read_bits(data, offset + 246, 4)  # 4 bits
        result['bTimeValidityYear'] = self.read_bits(data, offset + 250, 5)  # 5 bits
        result['bTimeValidityHour'] = self.read_bits(data, offset + 255, 5)  # 5 bits
        result['bTimeValidityMinute'] = self.read_bits(data, offset + 260, 6)  # 6 bits
        result['bTripBalance'] = self.read_bits(data, offset + 266, 8)  # 8 bits
        result['bDayTripCounter'] = self.read_bits(data, offset + 274, 3)  # 3 bits
        result['bLastValidationDay'] = self.read_bits(data, offset + 277, 5)  # 5 bits
        result['bPrevValidationOperator'] = self.read_bits(data, offset + 296, 5)  # 5 bits
        result['bPrevValidationType'] = self.read_bits(data, offset + 301, 5)  # 5 bits
        result['wPrevValidationPlace'] = self.read_bits(data, offset + 306, 13)  # 13 bits
        result['bPrevValidationDay'] = self.read_bits(data, offset + 319, 5)  # 5 bits
        result['bPrevValidationMonth'] = self.read_bits(data, offset + 324, 4)  # 4 bits
        result['bPrevValidationYear'] = self.read_bits(data, offset + 328, 5)  # 5 bits
        result['bPrevValidationHour'] = self.read_bits(data, offset + 333, 5)  # 5 bits
        result['bPrevValidationMinute'] = self.read_bits(data, offset + 338, 6)  # 6 bits
        result['bPrevNoOfPassengersTravelling'] = self.read_bits(data, offset + 350, 6)  # 6 bits
        result['bPrevNoOfPassengersExiting'] = self.read_bits(data, offset + 356, 6)  # 6 bits
        result['bPrevBlackListBit'] = self.read_bits(data, offset + 362, 1)  # 1 bit
        result['bPrevGreyListBit'] = self.read_bits(data, offset + 363, 1)  # 1 bit
        result['bPrevWhiteListBit'] = self.read_bits(data, offset + 364, 1)  # 1 bit
        result['bPrevEntryExitControl'] = self.read_bits(data, offset + 365, 1)  # 1 bit
        result['bOperator'] = self.read_bits(data, offset + 376, 5)  # 5 bits
        result['bType_2'] = self.read_bits(data, offset + 381, 5)  # 5 bits
        result['wValidationPlace'] = self.read_bits(data, offset + 386, 13)  # 13 bits
        result['bValidationDay'] = self.read_bits(data, offset + 399, 5)  # 5 bits
        result['bValidationMonth'] = self.read_bits(data, offset + 404, 4)  # 4 bits
        result['bValidationYear'] = self.read_bits(data, offset + 408, 5)  # 5 bits
        result['bValidationHour'] = self.read_bits(data, offset + 413, 5)  # 5 bits
        result['bValidationMinute'] = self.read_bits(data, offset + 418, 6)  # 6 bits
        result['bValidationSecond'] = self.read_bits(data, offset + 424, 6)  # 6 bits
        result['bNoOfPassengersTravelling'] = self.read_bits(data, offset + 430, 6)  # 6 bits
        result['bNoOfPassengersExiting'] = self.read_bits(data, offset + 436, 6)  # 6 bits
        result['bBlackListBit'] = self.read_bits(data, offset + 442, 1)  # 1 bit
        result['bGreyListBit'] = self.read_bits(data, offset + 443, 1)  # 1 bit
        result['bWhiteListBit'] = self.read_bits(data, offset + 444, 1)  # 1 bit
        result['bEntryExitControl'] = self.read_bits(data, offset + 445, 1)  # 1 bit

        result['l_spPurse->dwValue'] = self.read_bits(data, offset + 456, 32)  # 32 bit
        result['dwPurseDiscount'] = self.read_bits(data, offset + 488, 32)  # 32 bit
        result['CRC'] = self.read_bits(data, len(data) -16, 16)  # 16 bit

        return result

app = FastAPI()

# Importante si lo convierto a exe. Ruta base para PyInstaller (usa sys._MEIPASS si existe)
BASE_DIR = getattr(sys, '_MEIPASS', os.path.abspath("."))


# Ruta a los recursos estáticos y al index.html. Solo necesario si queremos cargar la web al lanzar localhost en raiz /
STATIC_DIR = os.path.join(BASE_DIR, "Myweb", "materialize")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")

app.mount("/css", StaticFiles(directory=os.path.join(STATIC_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")
app.mount("/images", StaticFiles(directory=os.path.join(STATIC_DIR, "images")), name="images")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por el dominio de tu frontend en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    print("Lanzando web")
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    
@app.get("/favicon.ico")
def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.ico"))


@app.get("/data/{item_id}")
def read_item(item_id: int, q: str = "hola"):
    return {"item_id": item_id, "query": q}

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}

@app.get("/param")
async def read_param_file():
    configClass = ConfigFileParser("documents/paramval.dat")
    buffer = configClass.read_binary_file()
    gen_param, zones = configClass.parse_param_file(buffer)
    return {"bCSCUpperVersion:": gen_param[0] ,
            "bCSCLowerVersion:": gen_param[1],
            "bCPSCUpperVersion:": gen_param[2],
            "bCPSCLowerVersion:": gen_param[3],
            "wPassbackTime:": gen_param[4],
            "wMinDiscount:": gen_param[5],
            "wMiddleMinDiscount:": gen_param[6],
            "wMiddleMaxDiscount:": gen_param[7],
            "wMaxDiscount:": gen_param[8],
            "wQRMaxValidityTime:": gen_param[9],
            "wQRMaxValidationTime:": gen_param[10],
            "wNumofActiveStations:": gen_param[11],
            "zones": zones}

@app.get("/titulos")
async def read_param_file():
    configClass = ConfigFileParser("documents/titulosval.dat")
    buffer = configClass.read_binary_file()
    data, baaTransferTimes = configClass.parse_titulos_file(buffer)
    print(baaTransferTimes)
    return {"Ticket size": data[0],
            "Config version": data[1],
            "Ticket Code": data[2],
            "Fare Type": data[3],
            "Spanish Name": data[4],
            "English Name": data[5],
            "French Name": data[6],
            "German Name": data[7],
            "Representation Type": data[8],
            "Area Control": data[9],
            "TransferTimes": baaTransferTimes,
            "Day Validity": data[10],
            "Week Validity": data[11],
            "Proprietary Company": data[12],
            "Valid Operators": data[13],
            "Balance Type": data[14],
            "Number of Trips": data[15],
            "Balance Period Value": data[16],
            "Balance Period Units": data[17],
            "Time Validity Exp Type At Sale": data[18],
            "Time Validity Begin Type At Val": data[19],
            "Time Validity Exp Type At Val": data[20],
            "Time Validity Begin At Val Ctrl": data[21],
            "Time Validity Exp At Val Ctrl": data[22],
            "No Entry Transfer Times": data[23],
            "Transfer Penalty Times": data[24],
            "Discounts": data[25],
            "Middle Discounts": data[26],
            "Max Entry to Exit Time": data[27]}
    
""" @app.get("/titulos2")
async def read_param_file():
    configClass = ConfigFileParser("documents/titulosval.dat")
    buffer = configClass.read_binary_file()
    data, baaTransferTimes = configClass.parse_titulos_file2(buffer)
    print(baaTransferTimes)
    print("data Size:", len(data))
    for i in range(len(data)):
        print(data[i])
    
    return {"data": data} """


@app.get("/titulos2")
async def read_param_file():
    configClass = ConfigFileParser("documents/titulosval.dat")
    buffer = configClass.read_binary_file()
    data, baaTransferTimes = configClass.parse_titulos_file2(buffer)
    print(baaTransferTimes)
    print("data Size:", len(data))
    for i in range(len(data)):
        print(data[i])
    
    return {"data": data}


'''puedo probar con curl
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  --request POST \
  -d "{\"registerString\": \"hola desde curl\"}"
  '''
  
@app.post("/register")
async def register_decoder(register_input: RegisterInput):
    register_string = register_input.registerString
    # Aquí puedes procesar el register_string como necesites
    print(f"Register String: {register_string}")
    
    registerClass = RegisterParser(register_string)
    baData = registerClass.hexstr_to_bytes()
    data = registerClass.parse(baData)    
    print(data)
    print("data Size:", len(data))

    # Mostrar algunos resultados
    for key in data:
        #print(f"{key}: {result[key]}")
        value = int(data[key])
        print(key, "-> dec:", value, "-> hex:", hex(value), "-> bin:", bin(value))
    
    return data #devuelve el dict directamente


if __name__ == "__main__":
    import uvicorn
    #uvicorn.run("fastAPI_test:app", host="127.0.0.1", port=8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)
