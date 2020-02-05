Name:       dbus

%define dbus_user_uid 82
%define dbus_user_name messagebus

Summary:    D-Bus message bus
Version:    1.13.12
Release:    1
Group:      System/Libraries
License:    GPLv2+ or AFL
URL:        http://www.freedesktop.org/software/dbus/
Source0:    http://dbus.freedesktop.org/releases/%{name}/%{name}-%{version}.tar.gz
Source1:    dbus-user.socket
Source2:    dbus-user.service
Source3:    dbus-system.socket
Source4:    dbus-system.service
Patch1:     0001-Enable-build-of-dbus-uuidgen-and-dbus-cleanup-socket.patch
# FIXME: Probably we should get rid of this patch and make proper setgid
# helper or so. Rumours say that this patch was about lipstick start and
# boosters orientation.
Patch2:     0002-patch-Disable-setuid-checking-due-to-it-conflicting-.patch
Patch3:     0003-Specify-configdir-correctly.patch
Patch4:     0004-Enable-building-with-systemd.patch
Patch5:     0005-Enable-building-with-selinux.patch
Patch6:     0006-Disable-selinux-from-config-file.patch
Patch7:     0007-Enable-building-with-libaudit.patch
Patch8:     0008-Check-for-monotonic-clock.patch
Requires:   %{name}-libs = %{version}
Requires:   systemd
Requires(pre): /usr/sbin/useradd
Requires(preun): systemd
Requires(post): systemd
Requires(postun): systemd
BuildRequires:  audit-libs-devel
BuildRequires:  cmake
BuildRequires:  expat-devel >= 1.95.5
BuildRequires:  gettext
BuildRequires:  libcap-ng-devel
BuildRequires:  libtool
BuildRequires:  pkgconfig(libselinux)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(systemd)

%description
D-Bus is a system for sending messages between applications. It is used both
for the systemwide message bus service, and as a per-user-login-session
messaging facility.

%package libs
Summary:    Libraries for accessing D-Bus
Group:      System/Libraries
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description libs
Lowlevel libraries for accessing D-Bus.

%package doc
Summary:    Developer documentation for D-Bus
Group:      Documentation
Requires:   %{name} = %{version}-%{release}

%description doc
This package contains DevHelp developer documentation for D-Bus along with
other supporting documentation such as the introspect dtd file.


%package devel
Summary:    Libraries and headers for D-Bus
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}
Requires:   pkgconfig

%description devel
Headers and static libraries for D-Bus.

%prep
%setup -q -n %{name}-%{version}/dbus
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1

%build
%cmake . -DCMAKE_INSTALL_PREFIX=/ \
-DCMAKE_INSTALL_LIBEXECDIR=%{_libexecdir}/dbus-1 \
-DCMAKE_BUILD_TYPE=Release \
-DDBUS_ENABLE_XML_DOCS=OFF \
-DDBUS_BUILD_TESTS=OFF \
-DDBUS_DISABLE_ASSERT=ON \
-DDBUS_BUS_ENABLE_INOTIFY=ON \
-DDBUS_ENABLE_PKGCONFIG=ON \
-DDBUS_ENABLE_VERBOSE_MODE=OFF
make %{?jobs:-j%jobs}

%install
rm -rf %{buildroot}
%make_install

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/dbus-1/interfaces
mkdir -p %{buildroot}%{_libdir}/systemd/user
install -m0644 %{SOURCE1} %{buildroot}%{_libdir}/systemd/user/dbus.socket
install -m0644 %{SOURCE2} %{buildroot}%{_libdir}/systemd/user/dbus.service

mkdir -p %{buildroot}%{_libdir}/systemd/system
install -m0644 %{SOURCE3} %{buildroot}%{_libdir}/systemd/system/dbus.socket
install -m0644 %{SOURCE4} %{buildroot}%{_libdir}/systemd/system/dbus.service

mkdir -p %{buildroot}%{_libdir}/systemd/system/sockets.target.wants
ln -fs ../dbus.socket %{buildroot}%{_libdir}/systemd/system/sockets.target.wants/dbus.socket
mkdir -p %{buildroot}%{_libdir}/systemd/system/dbus.target.wants
ln -fs ../dbus.socket %{buildroot}%{_libdir}/systemd/system/dbus.target.wants/dbus.socket

mkdir -p %{buildroot}%{_libdir}/systemd/system/basic.target.wants
ln -fs ../dbus.service %{buildroot}%{_libdir}/systemd/system/basic.target.wants/dbus.service

# Deprecated. Use %{_datadir}/dbus-1/ instead.
mkdir -p %{buildroot}%{_sysconfdir}/dbus-1/session.d
mkdir -p %{buildroot}%{_sysconfdir}/dbus-1/system.d

install -d %{buildroot}%{_libexecdir}/dbus-1
install -m4750 ./bin/dbus-daemon-launch-helper %{buildroot}%{_libexecdir}/dbus-1/dbus-daemon-launch-helper

%pre
# Add user and group for system daemon
[ -e /usr/sbin/groupadd ] && /usr/sbin/groupadd -r -g %{dbus_user_uid} %{dbus_user_name} 2>/dev/null || :
[ -e /usr/sbin/useradd ] && /usr/sbin/useradd -c 'System message bus' -u %{dbus_user_uid} \
-g %{dbus_user_uid} -s /sbin/nologin -r -d '/' %{dbus_user_name} 2> /dev/null || :

%preun
if [ "$1" -eq 0 ]; then
systemctl stop dbus.service || :
fi

%post
systemctl daemon-reload || :
# Do not restart dbus on post as it can cause a lot of services to break.
# We assume user is forced to reboot the system when system is updated.
systemctl reload dbus.service || :

%postun
systemctl daemon-reload || :

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%license COPYING
%{_bindir}/dbus-daemon
%{_bindir}/dbus-launch
%{_bindir}/dbus-monitor
%{_bindir}/dbus-run-session
%{_bindir}/dbus-send
%{_bindir}/dbus-test-tool
%{_bindir}/dbus-update-activation-environment
%{_bindir}/dbus-uuidgen
%dir %{_sysconfdir}/dbus-1
%config %{_sysconfdir}/dbus-1/session.conf
%dir %{_sysconfdir}/dbus-1/session.d
%config %{_sysconfdir}/dbus-1/system.conf
%dir %{_sysconfdir}/dbus-1/system.d
%dir %{_datadir}/dbus-1/session.d
%dir %{_datadir}/dbus-1/system.d
%dir %{_datadir}/dbus-1
%config %{_datadir}/dbus-1/session.conf
%config %{_datadir}/dbus-1/system.conf
%{_libdir}/systemd/user/*
%{_libdir}/systemd/system/dbus.service
%{_libdir}/systemd/system/dbus.socket
%{_libdir}/systemd/system/dbus.target.wants/dbus.socket
%{_libdir}/systemd/system/basic.target.wants/dbus.service
%{_libdir}/systemd/system/sockets.target.wants/dbus.socket
%dir %{_libexecdir}/dbus-1
%attr(4750,root,messagebus) %{_libexecdir}/dbus-1/dbus-daemon-launch-helper
%{_datadir}/dbus-1/interfaces
%{_datadir}/dbus-1/services
%{_datadir}/dbus-1/system-services
%ghost %dir %{_localstatedir}/run/dbus
%dir %{_localstatedir}/lib/dbus

%files libs
%defattr(-,root,root,-)
%{_libdir}/libdbus-1.so.3*

%files doc
%defattr(-,root,root,-)
%doc doc/introspect.dtd
%doc doc/introspect.xsl
%doc doc/system-activation.txt
%doc doc/diagram.png
%doc doc/diagram.svg
%doc %{_datadir}/doc/dbus/examples/*

%files devel
%defattr(-,root,root,-)
%{_libdir}/libdbus-1.so
%{_includedir}/dbus-1.0/dbus/dbus*.h
%dir %{_libdir}/dbus-1.0
%{_libdir}/dbus-1.0/include/dbus/dbus-arch-deps.h
%{_libdir}/pkgconfig/dbus-1.pc
%{_libdir}/cmake/DBus1/DBus1Config.cmake
%{_libdir}/cmake/DBus1/DBus1ConfigVersion.cmake
