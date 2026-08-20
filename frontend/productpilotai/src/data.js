import { backendData } from "./generated/backendData.js";

// Enhanced Catalog with Razorpay Test Mode & Agentic Commerce Bounds
const rawCatalog = backendData.industrialCatalog || [];

export const razorpayConfig = {
  keyId: "rzp_test_ProductPilot2026",
  merchantName: "ApexFlow Commerce Labs",
  currency: "INR",
  supportedProtocols: ["UAP-v1", "ACP-2026", "x402-gated"],
  settlementSpeed: "Instant T+0 Test Settlement"
};

export const industrialCatalog = rawCatalog.map((item, idx) => {
  const basePrices = [68500, 42000, 125000, 24000, 89000, 15500, 54000, 31000];
  const price = basePrices[idx % basePrices.length] || 55000;
  return {
    ...item,
    price_inr: price,
    price_formatted: `₹${price.toLocaleString("en-IN")}`,
    price_envelope: {
      min_price: Math.round(price * 0.9),
      max_price: Math.round(price * 1.15),
      currency: "INR",
      bounded: true
    },
    inventory: {
      in_stock: idx !== 3, // Simulate 1 out of stock for failure handling demo
      quantity_available: idx === 3 ? 0 : (24 + (idx * 7)),
      lead_time_days: idx === 3 ? "Backorder (3 wks)" : "Immediate Dispatch (24 hrs)"
    },
    upsell_recommendations: [
      {
        id: "UPS-01",
        title: "Extended 3-Year B2B Warranty & Precision Calibrator Kit",
        price_inr: Math.round(price * 0.12),
        price_formatted: `₹${Math.round(price * 0.12).toLocaleString("en-IN")}`,
        revenue_lift: "+12.0%"
      },
      {
        id: "UPS-02",
        title: "Smart IoT Vibration & Temperature Telemetry Node",
        price_inr: Math.round(price * 0.18),
        price_formatted: `₹${Math.round(price * 0.18).toLocaleString("en-IN")}`,
        revenue_lift: "+18.0%"
      }
    ],
    agent_readiness: {
      uap_compliant: true,
      acp_token: `ACP-${item.sku || 'SKU'}-2026`,
      provenance_hash: `0x9a8f${Math.random().toString(16).substring(2, 10)}7c`
    }
  };
});

export const industrialSources = backendData.industrialSources || [];
export const industrialStats = {
  ...(backendData.industrialStats || {}),
  total_agentic_gmv_inr: "₹4.82 Cr",
  agent_conversion_rate: "94.2%",
  avg_aov_lift: "+22.4%",
  guardrail_safety_rate: "100.0%",
  active_ai_buyers: 418
};
export const logoDataUrl = backendData.logoDataUrl || "";

// Real Company Logos for Sources (Base64 data URIs or CDN URLs)
export const sourceLogos = {
  // OEM Manufacturers
  "siemens": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Siemens-logo.svg/200px-Siemens-logo.svg.png",
  "bosch": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Bosch-logo.svg/200px-Bosch-logo.svg.png",
  "skf": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/SKF_logo.svg/200px-SKF_logo.svg.png",
  "festo": "https://upload.wikimedia.org/wikipedia/en/thumb/6/64/Festo_Logo.svg/200px-Festo_Logo.svg.png",
  "abb": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/ABB_logo.svg/200px-ABB_logo.svg.png",
  "schneider": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Schneider_Electric_2007.svg/200px-Schneider_Electric_2007.svg.png",
  
  // Distributors
  "grainger": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Grainger_Logo.svg/200px-Grainger_Logo.svg.png",
  "mcmaster": "https://www.mcmaster.com/mvwebres/content/images/mcmaster-carr-logo.svg",
  "rs_components": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/RS_Components_logo.svg/200px-RS_Components_logo.svg.png",
  "digikey": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Digi-Key_Logo.svg/200px-Digi-Key_Logo.svg.png",
  
  // ERP & PIM Systems
  "sap": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/SAP_2011_logo.svg/200px-SAP_2011_logo.svg.png",
  "oracle": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Oracle_logo.svg/200px-Oracle_logo.svg.png",
  "akeneo": "https://www.akeneo.com/wp-content/themes/akeneopim/images/logo.svg",
  "informatica": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Informatica_Logo.svg/200px-Informatica_Logo.svg.png",
  
  // CAD & Engineering
  "autocad": "https://damassets.autodesk.net/content/dam/autodesk/www/products/responsive-imagery/badge-75x75-01@2x.png",
  "solidworks": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d8/SolidWorks_Logo.svg/200px-SolidWorks_Logo.svg.png",
  "catia": "https://www.3ds.com/fileadmin/PRODUCTS/CATIA/IMAGES/2019/catia_logo.png",
  "creo": "https://www.ptc.com/-/media/3A2DA07BE3B94AF9BF08A8B87E7A7E7D.png",
  
  // Generic fallback
  "generic_oem": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='%23f0f0f0'/%3E%3Ctext x='50' y='55' font-size='14' font-family='Arial' text-anchor='middle' fill='%23666'%3EOEM%3C/text%3E%3C/svg%3E",
  "generic_distributor": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='%23e8f4f8'/%3E%3Ctext x='50' y='55' font-size='12' font-family='Arial' text-anchor='middle' fill='%230284c7'%3EDIST%3C/text%3E%3C/svg%3E",
  "generic_cad": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='%23f0fdf4'/%3E%3Ctext x='50' y='55' font-size='14' font-family='Arial' text-anchor='middle' fill='%2316a34a'%3ECAD%3C/text%3E%3C/svg%3E",
  "generic_erp": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='%23fef3c7'/%3E%3Ctext x='50' y='55' font-size='14' font-family='Arial' text-anchor='middle' fill='%23b45309'%3EERP%3C/text%3E%3C/svg%3E"
};

// Helper function to get logo URL for a source
export function getSourceLogo(sourceName) {
  const name = (sourceName || "").toLowerCase();
  
  // OEM matching
  if (name.includes("siemens")) return sourceLogos.siemens;
  if (name.includes("bosch")) return sourceLogos.bosch;
  if (name.includes("skf")) return sourceLogos.skf;
  if (name.includes("festo")) return sourceLogos.festo;
  if (name.includes("abb")) return sourceLogos.abb;
  if (name.includes("schneider")) return sourceLogos.schneider;
  
  // Distributor matching
  if (name.includes("grainger")) return sourceLogos.grainger;
  if (name.includes("mcmaster")) return sourceLogos.mcmaster;
  if (name.includes("rs components") || name.includes("rs-components")) return sourceLogos.rs_components;
  if (name.includes("digikey") || name.includes("digi-key")) return sourceLogos.digikey;
  
  // ERP/PIM matching
  if (name.includes("sap")) return sourceLogos.sap;
  if (name.includes("oracle")) return sourceLogos.oracle;
  if (name.includes("akeneo")) return sourceLogos.akeneo;
  if (name.includes("informatica")) return sourceLogos.informatica;
  
  // CAD matching
  if (name.includes("autocad") || name.includes("dwg")) return sourceLogos.autocad;
  if (name.includes("solidworks")) return sourceLogos.solidworks;
  if (name.includes("catia")) return sourceLogos.catia;
  if (name.includes("creo")) return sourceLogos.creo;
  
  // Fallback by type
  if (name.includes("oem") || name.includes("datasheet") || name.includes("technical")) return sourceLogos.generic_oem;
  if (name.includes("distributor") || name.includes("catalog") || name.includes("web")) return sourceLogos.generic_distributor;
  if (name.includes("cad") || name.includes("drawing") || name.includes("engineering")) return sourceLogos.generic_cad;
  if (name.includes("erp") || name.includes("pim") || name.includes("material")) return sourceLogos.generic_erp;
  
  return sourceLogos.generic_oem;
}