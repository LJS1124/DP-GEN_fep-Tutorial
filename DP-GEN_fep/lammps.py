def make_fep_lammps_input(
    ensemble,
    conf_file,
    neu_graphs,
    red_graphs,
    nsteps,
    dt,
    neidelay,
    trj_freq,
    mass_map,
    temp,
    fstate,
    jdata,
    tau_t=0.1,
    pres=None,
    tau_p=0.5,
    pka_e=None,
    ele_temp_f=None,
    ele_temp_a=None,
    max_seed=1000000,
    nopbc=False,
    deepmd_version="0.1",
):
    if (ele_temp_f is not None or ele_temp_a is not None) and Version(
        deepmd_version
    ) < Version("1"):
        raise RuntimeError(
            "the electron temperature is only supported by deepmd-kit >= 1.0.0, please upgrade your deepmd-kit"
        )
    if ele_temp_f is not None and ele_temp_a is not None:
        raise RuntimeError(
            "the frame style ele_temp and atom style ele_temp should not be set at the same time"
        )
    ret = "variable        NSTEPS          equal %d\n" % nsteps
    ret += "variable        THERMO_FREQ     equal %d\n" % trj_freq
    ret += "variable        DUMP_FREQ       equal %d\n" % trj_freq
    ret += "variable        TEMP            equal %f\n" % temp
    if ele_temp_f is not None:
        ret += "variable        ELE_TEMP        equal %f\n" % ele_temp_f
    if ele_temp_a is not None:
        ret += "variable        ELE_TEMP        equal %f\n" % ele_temp_a
    ret += "variable        PRES            equal %f\n" % pres
    ret += "variable        TAU_T           equal %f\n" % tau_t
    ret += "variable        TAU_P           equal %f\n" % tau_p
    ret += "variable        plus            equal %d\n" % 1
    ret += "variable        minus           equal %d\n" % -1
    ret += "variable        LAMBDA_i        equal %f\n" % fstate
    ret += "variable        LAMBDA_f        equal 1-v_LAMBDA_i \n"

    ret += "\n"
    ret += "units           metal\n"
    if nopbc:
        ret += "boundary        f f f\n"
    else:
        ret += "boundary        p p p\n"
    ret += "atom_style      atomic\n"
    ret += "\n"
    ret += "neighbor        1.0 bin\n"
    if neidelay is not None:
        ret += "neigh_modify    delay %d\n" % neidelay
    ret += "\n"
    ret += "box          tilt large\n"
    ret += (
        'if "${restart} > 0" then "read_restart dpgen.restart.*" else "read_data %s"\n'
        % conf_file
    )
    ret += "change_box   all triclinic\n"
    for jj in range(len(mass_map)):
        ret += "mass            %d %f\n" % (jj + 1, mass_map[jj])
    neu_list = ""
    red_list = ""
    for ii in neu_graphs:
        neu_list += ii + " "
    for ii in red_graphs:
        red_list += ii + " "   
        # 1.x
        keywords = ""
    if jdata.get("use_clusters", False):
        keywords += "atomic "
    if jdata.get("use_relative", False):
        keywords += "relative %s " % jdata["epsilon"]
    if jdata.get("use_relative_v", False):
        keywords += "relative_v %s " % jdata["epsilon_v"]
    if ele_temp_f is not None:
        keywords += "fparam ${ELE_TEMP}"
    if ele_temp_a is not None:
            keywords += "aparam ${ELE_TEMP}"
    ret += "pair_style hybrid/overlay &\n"
    ret += "           deepmd %s out_freq ${THERMO_FREQ} out_file dev_neu.out %s&\n"% (neu_list,keywords)
    ret += "           deepmd %s out_freq ${THERMO_FREQ} out_file dev_red.out %s\n"% (red_list,keywords)

    ret += "pair_coeff      * * deepmd 1 *\n"
    ret += "pair_coeff      * * deepmd 2 *\n"
    ret += "\n"
    ret += "fix     sampling_PES all adapt 0 &\n \t\tpair deepmd:1 scale * * v_LAMBDA_i &\n \t\tpair deepmd:2 scale * * v_LAMBDA_f &\n \t\tscale yes\n"
    ret += "thermo_style    custom step temp pe ke etotal press vol lx ly lz xy xz yz\n"
    ret += "thermo          ${THERMO_FREQ}\n"
    model_devi_merge_traj = jdata.get("model_devi_merge_traj", False)
    if model_devi_merge_traj is True:
        ret += "dump            1 all custom ${DUMP_FREQ} all.lammpstrj id type x y z fx fy fz\n"
        ret += 'if "${restart} > 0" then "dump_modify     1 append yes"\n'
    else:
        ret += "dump            1 all custom ${DUMP_FREQ} traj/*.lammpstrj id type x y z fx fy fz\n"
    ret += "restart         10000 dpgen.restart\n"
    ret += "\n"
    if pka_e is None:
        ret += 'if "${restart} == 0" then "velocity        all create ${TEMP} %d"' % (
            random.randrange(max_seed - 1) + 1
        )
    else:
        sys = dpdata.System(conf_file, fmt="lammps/lmp")
        sys_data = sys.data
        pka_mass = mass_map[sys_data["atom_types"][0] - 1]
        pka_vn = (
            pka_e
            * pc.electron_volt
            / (0.5 * pka_mass * 1e-3 / pc.Avogadro * (pc.angstrom / pc.pico) ** 2)
        )
        pka_vn = np.sqrt(pka_vn)
        print(pka_vn)
        pka_vec = _sample_sphere()
        pka_vec *= pka_vn
        ret += "group           first id 1\n"
        ret += 'if "${restart} == 0" then "velocity        first set %f %f %f"\n' % (
            pka_vec[0],
            pka_vec[1],
            pka_vec[2],
        )
        ret += "fix	       2 all momentum 1 linear 1 1 1\n"
    ret += "\n"
    if ensemble.split("-")[0] == "npt":
        assert pres is not None
        if nopbc:
            raise RuntimeError("ensemble %s is conflicting with nopbc" % ensemble)
    if ensemble == "npt" or ensemble == "npt-i" or ensemble == "npt-iso":
        ret += "fix             1 all npt temp ${TEMP} ${TEMP} ${TAU_T} iso ${PRES} ${PRES} ${TAU_P}\n"
    elif ensemble == "npt-a" or ensemble == "npt-aniso":
        ret += "fix             1 all npt temp ${TEMP} ${TEMP} ${TAU_T} aniso ${PRES} ${PRES} ${TAU_P}\n"
    elif ensemble == "npt-t" or ensemble == "npt-tri":
        ret += "fix             1 all npt temp ${TEMP} ${TEMP} ${TAU_T} tri ${PRES} ${PRES} ${TAU_P}\n"
    elif ensemble == "nvt":
        ret += "fix             1 all nvt temp ${TEMP} ${TEMP} ${TAU_T}\n"
    elif ensemble == "nve":
        ret += "fix             1 all nve\n"
    else:
        raise RuntimeError("unknown emsemble " + ensemble)
    if nopbc:
        ret += "velocity        all zero linear\n"
        ret += "fix             fm all momentum 1 linear 1 1 1\n"
    ret += "\n"
    ret += "timestep        %f\n" % dt
    ret += "run             ${NSTEPS} upto\n"
    return ret