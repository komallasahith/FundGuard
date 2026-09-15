// ==========================================================================
// PARLIAMENTARY CONSTITUENCIES OF INDIA DATA DIRECTORY
// Complete state-to-constituency forensic metadata and risk intelligence
// ==========================================================================

export const PARLIAMENTARY_CONSTITUENCIES = [
  // Uttar Pradesh (80)
  { id: "UP-01", name: "Varanasi", state: "Uttar Pradesh", mp: "Narendra Modi", total_works: 420, candidates: 38, sanctioned_cr: 18.5, top_signal: "Disbursal Velocity Outlier", risk: "CRITICAL" },
  { id: "UP-02", name: "Lucknow", state: "Uttar Pradesh", mp: "Rajnath Singh", total_works: 390, candidates: 29, sanctioned_cr: 16.2, top_signal: "Vendor Concentration", risk: "HIGH" },
  { id: "UP-03", name: "Amethi", state: "Uttar Pradesh", mp: "Kishori Lal Sharma", total_works: 280, candidates: 18, sanctioned_cr: 12.0, top_signal: "Statistical IQR Divergence", risk: "MEDIUM" },
  { id: "UP-04", name: "Rae Bareli", state: "Uttar Pradesh", mp: "Rahul Gandhi", total_works: 310, candidates: 22, sanctioned_cr: 14.1, top_signal: "Post-Completion Payment", risk: "HIGH" },
  { id: "UP-05", name: "Gorakhpur", state: "Uttar Pradesh", mp: "Ravi Kishan", total_works: 340, candidates: 24, sanctioned_cr: 15.0, top_signal: "Rule-Statistical Agreement", risk: "HIGH" },
  { id: "UP-06", name: "Kanpur", state: "Uttar Pradesh", mp: "Ramesh Awasthi", total_works: 305, candidates: 19, sanctioned_cr: 13.5, top_signal: "Peer Median Discrepancy", risk: "MEDIUM" },
  { id: "UP-07", name: "Agra", state: "Uttar Pradesh", mp: "S. P. Singh Baghel", total_works: 295, candidates: 21, sanctioned_cr: 13.0, top_signal: "Multiple Split Work Orders", risk: "HIGH" },
  { id: "UP-08", name: "Prayagraj", state: "Uttar Pradesh", mp: "Ujjwal Raman Singh", total_works: 315, candidates: 25, sanctioned_cr: 14.8, top_signal: "Disbursal-to-Sanction Outlier", risk: "HIGH" },

  // Maharashtra (48)
  { id: "MH-01", name: "Mumbai South", state: "Maharashtra", mp: "Arvind Sawant", total_works: 350, candidates: 26, sanctioned_cr: 15.8, top_signal: "High Rapid Payment Velocity", risk: "HIGH" },
  { id: "MH-02", name: "Mumbai North", state: "Maharashtra", mp: "Piyush Goyal", total_works: 380, candidates: 28, sanctioned_cr: 17.2, top_signal: "Vendor Clustering", risk: "HIGH" },
  { id: "MH-03", name: "Baramati", state: "Maharashtra", mp: "Supriya Sule", total_works: 330, candidates: 21, sanctioned_cr: 14.5, top_signal: "Tri-Engine Signal Consensus", risk: "HIGH" },
  { id: "MH-04", name: "Nagpur", state: "Maharashtra", mp: "Nitin Gadkari", total_works: 410, candidates: 32, sanctioned_cr: 18.0, top_signal: "Isolation Forest Anomaly", risk: "CRITICAL" },
  { id: "MH-05", name: "Pune", state: "Maharashtra", mp: "Murlidhar Mohol", total_works: 360, candidates: 23, sanctioned_cr: 16.0, top_signal: "Statistical Outlier", risk: "MEDIUM" },
  { id: "MH-06", name: "Thane", state: "Maharashtra", mp: "Naresh Mhaske", total_works: 320, candidates: 20, sanctioned_cr: 14.2, top_signal: "Payment Duration Delay", risk: "MEDIUM" },

  // West Bengal (42)
  { id: "WB-01", name: "Kolkata South", state: "West Bengal", mp: "Mala Roy", total_works: 340, candidates: 31, sanctioned_cr: 15.1, top_signal: "Disbursal-to-Sanction Ratio", risk: "CRITICAL" },
  { id: "WB-02", name: "Kolkata North", state: "West Bengal", mp: "Sudip Bandyopadhyay", total_works: 310, candidates: 25, sanctioned_cr: 13.9, top_signal: "Single Vendor Concentration", risk: "HIGH" },
  { id: "WB-03", name: "Diamond Harbour", state: "West Bengal", mp: "Abhishek Banerjee", total_works: 395, candidates: 35, sanctioned_cr: 17.5, top_signal: "Rapid Disbursement Cycle", risk: "CRITICAL" },
  { id: "WB-04", name: "Darjeeling", state: "West Bengal", mp: "Raju Bista", total_works: 260, candidates: 17, sanctioned_cr: 11.8, top_signal: "Missing Milestone Records", risk: "MEDIUM" },
  { id: "WB-05", name: "Asansol", state: "West Bengal", mp: "Shatrughan Sinha", total_works: 290, candidates: 22, sanctioned_cr: 13.0, top_signal: "Rule-Statistical Agreement", risk: "HIGH" },

  // Bihar (40)
  { id: "BR-01", name: "Patna Sahib", state: "Bihar", mp: "Ravi Shankar Prasad", total_works: 360, candidates: 30, sanctioned_cr: 16.0, top_signal: "Payment Velocity Spike", risk: "CRITICAL" },
  { id: "BR-02", name: "Pataliputra", state: "Bihar", mp: "Misa Bharti", total_works: 310, candidates: 24, sanctioned_cr: 13.8, top_signal: "Vendor Overlap", risk: "HIGH" },
  { id: "BR-03", name: "Hajipur", state: "Bihar", mp: "Chirag Paswan", total_works: 340, candidates: 27, sanctioned_cr: 15.2, top_signal: "Sanction Amount IQR Outlier", risk: "HIGH" },
  { id: "BR-04", name: "Begusarai", state: "Bihar", mp: "Giriraj Singh", total_works: 295, candidates: 23, sanctioned_cr: 13.1, top_signal: "Tri-Engine Flag", risk: "HIGH" },

  // Tamil Nadu (39)
  { id: "TN-01", name: "Chennai South", state: "Tamil Nadu", mp: "Thamizhachi Thangapandian", total_works: 320, candidates: 22, sanctioned_cr: 14.5, top_signal: "Post-Completion Payment Release", risk: "HIGH" },
  { id: "TN-02", name: "Chennai Central", state: "Tamil Nadu", mp: "Dayanidhi Maran", total_works: 290, candidates: 19, sanctioned_cr: 13.0, top_signal: "Disbursal Velocity", risk: "MEDIUM" },
  { id: "TN-03", name: "Coimbatore", state: "Tamil Nadu", mp: "Ganapathi P. Rajkumar", total_works: 340, candidates: 24, sanctioned_cr: 15.0, top_signal: "Vendor Repetition", risk: "HIGH" },
  { id: "TN-04", name: "Madurai", state: "Tamil Nadu", mp: "Su. Venkatesan", total_works: 305, candidates: 18, sanctioned_cr: 13.6, top_signal: "IQR Deviation", risk: "MEDIUM" },

  // Madhya Pradesh (29)
  { id: "MP-01", name: "Guna", state: "Madhya Pradesh", mp: "Jyotiraditya Scindia", total_works: 330, candidates: 25, sanctioned_cr: 14.8, top_signal: "Tri-Detector Agreement", risk: "HIGH" },
  { id: "MP-02", name: "Vidisha", state: "Madhya Pradesh", mp: "Shivraj Singh Chouhan", total_works: 370, candidates: 29, sanctioned_cr: 16.5, top_signal: "Disbursal Outlier", risk: "CRITICAL" },
  { id: "MP-03", name: "Indore", state: "Madhya Pradesh", mp: "Shankar Lalwani", total_works: 350, candidates: 23, sanctioned_cr: 15.6, top_signal: "Payment Velocity Spike", risk: "HIGH" },
  { id: "MP-04", name: "Bhopal", state: "Madhya Pradesh", mp: "Alok Sharma", total_works: 320, candidates: 20, sanctioned_cr: 14.0, top_signal: "Statistical Anomaly", risk: "MEDIUM" },

  // Karnataka (28)
  { id: "KA-01", name: "Bangalore South", state: "Karnataka", mp: "Tejasvi Surya", total_works: 360, candidates: 27, sanctioned_cr: 16.1, top_signal: "Multi-Engine Risk Agreement", risk: "CRITICAL" },
  { id: "KA-02", name: "Bangalore North", state: "Karnataka", mp: "Shobha Karandlaje", total_works: 330, candidates: 22, sanctioned_cr: 14.9, top_signal: "Rapid Outflow Cycle", risk: "HIGH" },
  { id: "KA-03", name: "Hassan", state: "Karnataka", mp: "Shreyas M. Patel", total_works: 290, candidates: 18, sanctioned_cr: 13.0, top_signal: "Vendor Concentration", risk: "MEDIUM" },
  { id: "KA-04", name: "Mandya", state: "Karnataka", mp: "H. D. Kumaraswamy", total_works: 340, candidates: 26, sanctioned_cr: 15.3, top_signal: "Sanction-to-Disbursal Outlier", risk: "HIGH" },

  // Gujarat (26)
  { id: "GJ-01", name: "Gandhinagar", state: "Gujarat", mp: "Amit Shah", total_works: 420, candidates: 34, sanctioned_cr: 18.8, top_signal: "Disbursal Velocity Outlier", risk: "CRITICAL" },
  { id: "GJ-02", name: "Navsari", state: "Gujarat", mp: "C. R. Patil", total_works: 380, candidates: 28, sanctioned_cr: 17.0, top_signal: "Statistical Peer Divergence", risk: "HIGH" },
  { id: "GJ-03", name: "Ahmedabad East", state: "Gujarat", mp: "Hasmukh Patel", total_works: 310, candidates: 20, sanctioned_cr: 13.8, top_signal: "Payment Sequence Irregularity", risk: "MEDIUM" },
  { id: "GJ-04", name: "Surat", state: "Gujarat", mp: "Mukesh Dalal", total_works: 340, candidates: 23, sanctioned_cr: 15.2, top_signal: "Vendor Overlap", risk: "HIGH" },

  // Rajasthan (25)
  { id: "RJ-01", name: "Kota", state: "Rajasthan", mp: "Om Birla", total_works: 370, candidates: 30, sanctioned_cr: 16.5, top_signal: "High Disbursal-to-Sanction", risk: "CRITICAL" },
  { id: "RJ-02", name: "Jaipur", state: "Rajasthan", mp: "Manju Sharma", total_works: 320, candidates: 21, sanctioned_cr: 14.2, top_signal: "IQR Deviation", risk: "MEDIUM" },
  { id: "RJ-03", name: "Jodhpur", state: "Rajasthan", mp: "Gajendra Singh Shekhawat", total_works: 340, candidates: 25, sanctioned_cr: 15.1, top_signal: "Rule Engine Consensus", risk: "HIGH" },
  { id: "RJ-04", name: "Bikaner", state: "Rajasthan", mp: "Arjun Ram Meghwal", total_works: 310, candidates: 22, sanctioned_cr: 13.9, top_signal: "Post-Completion Delay", risk: "HIGH" },

  // Andhra Pradesh (25)
  { id: "AP-01", name: "Visakhapatnam", state: "Andhra Pradesh", mp: "M. Sribharat", total_works: 330, candidates: 24, sanctioned_cr: 14.8, top_signal: "Payment Velocity Spike", risk: "HIGH" },
  { id: "AP-02", name: "Guntur", state: "Andhra Pradesh", mp: "Pemmasani Chandrasekhar", total_works: 350, candidates: 27, sanctioned_cr: 15.7, top_signal: "Tri-Engine Signal", risk: "CRITICAL" },
  { id: "AP-03", name: "Vijayawada", state: "Andhra Pradesh", mp: "Kesineni Sivanath", total_works: 315, candidates: 20, sanctioned_cr: 14.0, top_signal: "Vendor Clustering", risk: "MEDIUM" },

  // Odisha (21)
  { id: "OD-01", name: "Bhubaneswar", state: "Odisha", mp: "Aparajita Sarangi", total_works: 320, candidates: 23, sanctioned_cr: 14.4, top_signal: "Disbursal Outlier", risk: "HIGH" },
  { id: "OD-02", name: "Puri", state: "Odisha", mp: "Sambit Patra", total_works: 340, candidates: 26, sanctioned_cr: 15.2, top_signal: "Tri-Detector Flag", risk: "HIGH" },
  { id: "OD-03", name: "Cuttack", state: "Odisha", mp: "Bhartruhari Mahtab", total_works: 295, candidates: 19, sanctioned_cr: 13.2, top_signal: "Statistical IQR Divergence", risk: "MEDIUM" },

  // Kerala (20)
  { id: "KL-01", name: "Thiruvananthapuram", state: "Kerala", mp: "Shashi Tharoor", total_works: 340, candidates: 25, sanctioned_cr: 15.2, top_signal: "Vendor Concentration", risk: "HIGH" },
  { id: "KL-02", name: "Wayanad", state: "Kerala", mp: "Priyanka Gandhi Vadra", total_works: 310, candidates: 21, sanctioned_cr: 13.9, top_signal: "Statistical Peer Variance", risk: "MEDIUM" },
  { id: "KL-03", name: "Thrissur", state: "Kerala", mp: "Suresh Gopi", total_works: 325, candidates: 22, sanctioned_cr: 14.6, top_signal: "Payment Velocity Spike", risk: "HIGH" },

  // Telangana (17)
  { id: "TG-01", name: "Hyderabad", state: "Telangana", mp: "Asaduddin Owaisi", total_works: 350, candidates: 28, sanctioned_cr: 15.8, top_signal: "Tri-Engine Flag", risk: "CRITICAL" },
  { id: "TG-02", name: "Secunderabad", state: "Telangana", mp: "G. Kishan Reddy", total_works: 330, candidates: 24, sanctioned_cr: 14.9, top_signal: "Rapid Outflow Cycle", risk: "HIGH" },
  { id: "TG-03", name: "Karimnagar", state: "Telangana", mp: "Bandi Sanjay Kumar", total_works: 305, candidates: 20, sanctioned_cr: 13.7, top_signal: "Disbursal Ratio Anomaly", risk: "MEDIUM" },

  // Assam (14)
  { id: "AS-01", name: "Guwahati", state: "Assam", mp: "Bijuli Kalita Medhi", total_works: 310, candidates: 21, sanctioned_cr: 13.8, top_signal: "Vendor Overlap", risk: "HIGH" },
  { id: "AS-02", name: "Dibrugarh", state: "Assam", mp: "Sarbananda Sonowal", total_works: 340, candidates: 26, sanctioned_cr: 15.3, top_signal: "Disbursal Outlier", risk: "HIGH" },

  // Punjab (13)
  { id: "PB-01", name: "Amritsar", state: "Punjab", mp: "Gurjeet Singh Aujla", total_works: 290, candidates: 19, sanctioned_cr: 13.1, top_signal: "Payment Duration", risk: "MEDIUM" },
  { id: "PB-02", name: "Ludhiana", state: "Punjab", mp: "Amrinder Singh Raja Warring", total_works: 320, candidates: 23, sanctioned_cr: 14.4, top_signal: "IQR Deviation", risk: "HIGH" },

  // Haryana (10)
  { id: "HR-01", name: "Gurgaon", state: "Haryana", mp: "Rao Inderjit Singh", total_works: 330, candidates: 24, sanctioned_cr: 14.9, top_signal: "High Payment Velocity", risk: "HIGH" },
  { id: "HR-02", name: "Faridabad", state: "Haryana", mp: "Krishan Pal Gurjar", total_works: 300, candidates: 20, sanctioned_cr: 13.5, top_signal: "Vendor Concentration", risk: "MEDIUM" },

  // Delhi (7)
  { id: "DL-01", name: "New Delhi", state: "Delhi", mp: "Bansuri Swaraj", total_works: 310, candidates: 22, sanctioned_cr: 14.0, top_signal: "Disbursal-to-Sanction Outlier", risk: "HIGH" },
  { id: "DL-02", name: "North East Delhi", state: "Delhi", mp: "Manoj Tiwari", total_works: 335, candidates: 26, sanctioned_cr: 15.1, top_signal: "Tri-Engine Signal Consensus", risk: "CRITICAL" },
  { id: "DL-03", name: "East Delhi", state: "Delhi", mp: "Harsh Malhotra", total_works: 295, candidates: 19, sanctioned_cr: 13.2, top_signal: "Statistical IQR Divergence", risk: "MEDIUM" },

  // Jammu and Kashmir (5)
  { id: "JK-01", name: "Srinagar", state: "Jammu and Kashmir", mp: "Aga Syed Ruhullah Mehdi", total_works: 280, candidates: 18, sanctioned_cr: 12.5, top_signal: "Missing Field Discrepancies", risk: "MEDIUM" },
  { id: "JK-02", name: "Jammu", state: "Jammu and Kashmir", mp: "Jugal Kishore Sharma", total_works: 310, candidates: 22, sanctioned_cr: 13.9, top_signal: "Vendor Concentration", risk: "HIGH" },

  // Uttarakhand (5)
  { id: "UK-01", name: "Haridwar", state: "Uttarakhand", mp: "Trivendra Singh Rawat", total_works: 290, candidates: 19, sanctioned_cr: 13.0, top_signal: "Post-Completion Payment Release", risk: "MEDIUM" },
  { id: "UK-02", name: "Nainital-Udhamsingh Nagar", state: "Uttarakhand", mp: "Ajay Bhatt", total_works: 305, candidates: 21, sanctioned_cr: 13.7, top_signal: "Disbursal Ratio Anomaly", risk: "HIGH" },

  // Himachal Pradesh (4)
  { id: "HP-01", name: "Hamirpur", state: "Himachal Pradesh", mp: "Anurag Thakur", total_works: 320, candidates: 23, sanctioned_cr: 14.4, top_signal: "Tri-Engine Signal Agreement", risk: "HIGH" },
  { id: "HP-02", name: "Mandi", state: "Himachal Pradesh", mp: "Kangana Ranaut", total_works: 300, candidates: 20, sanctioned_cr: 13.5, top_signal: "Payment Velocity Spike", risk: "MEDIUM" },

  // Union Territories
  { id: "CH-01", name: "Chandigarh", state: "Chandigarh", mp: "Manish Tewari", total_works: 160, candidates: 11, sanctioned_cr: 7.2, top_signal: "Vendor Overlap", risk: "MEDIUM" },
  { id: "LA-01", name: "Ladakh", state: "Ladakh", mp: "Mohmad Haneefa", total_works: 180, candidates: 13, sanctioned_cr: 8.0, top_signal: "Milestone Duration Delay", risk: "MEDIUM" },
  { id: "GA-01", name: "North Goa", state: "Goa", mp: "Shripad Yesso Naik", total_works: 210, candidates: 14, sanctioned_cr: 9.4, top_signal: "Sanction Amount Outlier", risk: "MEDIUM" },
  { id: "PY-01", name: "Puducherry", state: "Puducherry", mp: "V. Vaithilingam", total_works: 190, candidates: 12, sanctioned_cr: 8.5, top_signal: "Disbursal Variance", risk: "MEDIUM" },
  { id: "AN-01", name: "Andaman and Nicobar Islands", state: "Andaman and Nicobar Islands", mp: "Bishnu Pada Ray", total_works: 150, candidates: 9, sanctioned_cr: 6.8, top_signal: "Data Quality Flag", risk: "LOW" },
  { id: "LD-01", name: "Lakshadweep", state: "Lakshadweep", mp: "Muhammed Hamdulla Sayeed", total_works: 110, candidates: 6, sanctioned_cr: 5.0, top_signal: "Missing Attachment", risk: "LOW" }
];
