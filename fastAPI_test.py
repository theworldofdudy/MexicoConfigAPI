from enum import Enum
import struct
import sys

from fastapi import FastAPI

## backend -> frontend
from fastapi.middleware.cors import CORSMiddleware

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

            baaTransferTimes = [list(ticket[8][i * 8:(i + 1) * 8]) for i in range(8)]
            baNoEntryTransferTimes = list(ticket[56:64])
            baTransferPenaltyTimes = list(ticket[64:72])
            raw_discounts = ticket[72:82]  # 10 DWORDs
            raw_midle_discounts = ticket[82:92]  # 10 DWORDs

            tsaDiscount = [(raw_discounts[i], raw_discounts[i + 1]) for i in range(0, len(raw_discounts), 2)]
            tsaMidleDiscount = [(raw_midle_discounts[i], raw_midle_discounts[i + 1]) for i in range(0, len(raw_midle_discounts), 2)]

            output.append(f"Ticket Code: {ticket[0]}")
            output.append(f"Fare Type: {ticket[1]}")
            output.append(f"Spanish Name: {baSpanishName}")
            output.append(f"English Name: {baEnglishName}")
            output.append(f"French Name: {baFrenchName}")
            output.append(f"German Name: {baGermanName}")
            output.append(f"Representation Type: {ticket[6]}")
            output.append(f"Area Control: {ticket[7]}")
            output.append(f"Transfer Times: {baaTransferTimes}")
            output.append(f"Day Validity: {ticket[9]}")
            output.append(f"Week Validity: {ticket[10]}")
            output.append(f"Proprietary Company: {ticket[11]}")
            output.append(f"Valid Operators: {ticket[12]}")
            output.append(f"Balance Type: {ticket[13]}")
            output.append(f"Number of Trips: {ticket[14]}")
            output.append(f"Balance Period Value: {ticket[15]}")
            output.append(f"Balance Period Units: {ticket[16]}")
            output.append(f"Time Validity Exp Type At Sale: {ticket[17]}")
            output.append(f"Time Validity Begin Type At Val: {ticket[18]}")
            output.append(f"Time Validity Exp Type At Val: {ticket[19]}")
            output.append(f"Time Validity Begin At Val Ctrl: {ticket[20]}")
            output.append(f"Time Validity Exp At Val Ctrl: {ticket[21]}")
            output.append(f"No Entry Transfer Times: {baNoEntryTransferTimes}")
            output.append(f"Transfer Penalty Times: {baTransferPenaltyTimes}")
            output.append(f"Discounts: {tsaDiscount}")
            output.append(f"Middle Discounts: {tsaMidleDiscount}")
            output.append(f"Max Entry to Exit Time: {ticket[32]}")
            output.append("-" * 50)

            offset += tsICfgTicket_size

        return output



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por el dominio de tu frontend en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "¡Hola desde la API de Carlos!"}

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
    configClass = ConfigFileParser("paramval.dat")
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
    configClass = ConfigFileParser("titulosval.dat")
    buffer = configClass.read_binary_file()
    data = configClass.parse_titulos_file(buffer)
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
            "Transfer Times": data[10],
            "Day Validity": data[11],
            "Week Validity": data[12],
            "Proprietary Company": data[13],
            "Valid Operators": data[14],
            "Balance Type": data[15],
            "Number of Trips": data[16],
            "Balance Period Value": data[17],
            "Balance Period Units": data[18],
            "Time Validity Exp Type At Sale": data[19],
            "Time Validity Begin Type At Val": data[20],
            "Time Validity Exp Type At Val": data[21],
            "Time Validity Begin At Val Ctrl": data[22],
            "Time Validity Exp At Val Ctrl": data[23],
            "No Entry Transfer Times": data[24],
            "Transfer Penalty Times": data[25],
            "Discounts": data[26],
            "Middle Discounts": data[27],
            "Max Entry to Exit Time": data[28]}